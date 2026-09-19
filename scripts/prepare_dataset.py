import os
import sys
import django
import pandas as pd

from datetime import timedelta


# ============================================================
# DJANGO SETUP
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "TrafficAI.settings"
)

django.setup()


from predictions.models import (
    TrafficData,
    WeatherData,
)


# ============================================================
# COLLECT TRAFFIC DATA
# ============================================================

rows = []


traffic_records = list(
    TrafficData.objects
    .select_related("location")
    .order_by(
        "location_id",
        "recorded_time"
    )
)


print(
    f"Found {len(traffic_records)} traffic observations."
)


# ============================================================
# BUILD TRAINING ROWS
# ============================================================

for index, traffic in enumerate(traffic_records):

    location = traffic.location


    # --------------------------------------------------------
    # Find the NEXT traffic observation
    # for the same location
    # --------------------------------------------------------

    next_traffic = None

    for future_traffic in traffic_records[index + 1:]:

        if future_traffic.location_id != location.id:
            continue

        if (
            future_traffic.recorded_time
            > traffic.recorded_time
        ):
            next_traffic = future_traffic
            break


    # We need a future observation
    if next_traffic is None:
        continue


    # --------------------------------------------------------
    # Find closest weather observation
    # --------------------------------------------------------

    weather_data = WeatherData.objects.filter(
        location=location
    )


    if not weather_data.exists():
        continue


    closest_weather = min(
        weather_data,
        key=lambda w: abs(
            w.recorded_time -
            traffic.recorded_time
        )
    )


    # --------------------------------------------------------
    # Make sure weather is reasonably close
    # --------------------------------------------------------

    weather_difference = abs(
        closest_weather.recorded_time -
        traffic.recorded_time
    )


    if weather_difference > timedelta(
        minutes=10
    ):
        continue


    # --------------------------------------------------------
    # Add training row
    # --------------------------------------------------------

    rows.append({

        # Location
        "location":
            location.location_name,

        # Current timestamp
        "recorded_time":
            traffic.recorded_time,

        # Current traffic speed
        "current_speed":
            traffic.current_speed,

        # Previous/current speed feature
        "previous_speed":
            traffic.current_speed,

        # NEXT observed speed = TARGET
        "next_speed":
            next_traffic.current_speed,

        # Other traffic information
        "free_flow_speed":
            traffic.free_flow_speed,

        "congestion_ratio":
            traffic.congestion_ratio,

        "confidence":
            traffic.confidence,

        # Location information
        "speed_limit":
            location.speed_limit,

        "road_type":
            location.road_type,

        "lanes":
            location.lanes,

        "aadt":
            location.aadt,

        "historical_crashes_2yr":
            location.historical_crashes_2yr,

        # Weather
        "temperature":
            closest_weather.temperature,

        "humidity":
            closest_weather.humidity,

        "precipitation":
            closest_weather.precipitation,

        "wind_speed":
            closest_weather.wind_speed,
    })


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(rows)


# ============================================================
# CREATE TIME FEATURES
# ============================================================

if not df.empty:

    df["recorded_time"] = pd.to_datetime(
        df["recorded_time"]
    )


    # Hour
    df["hour"] = (
        df["recorded_time"].dt.hour
    )


    # Day of week
    # Monday = 0
    # Sunday = 6
    df["day_of_week"] = (
        df["recorded_time"]
        .dt.dayofweek
    )


    # Weekend
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)


# ============================================================
# SAVE DATASET
# ============================================================

output_path = os.path.join(
    PROJECT_ROOT,
    "ml",
    "traffic_training_data.csv"
)


df.to_csv(
    output_path,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()
print("=" * 60)
print("DATASET CREATED")
print("=" * 60)

print()
print("Rows:", len(df))

print()
print("Columns:")
print(df.columns.tolist())

print()
print("First 5 rows:")
print(df.head())

print()
print(
    f"Saved to: {output_path}"
)