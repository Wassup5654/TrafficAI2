import os
import django
import pandas as pd
import sys
from datetime import timedelta

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "TrafficAI.settings"
)

django.setup()

from predictions.models import TrafficData, WeatherData


rows = []

# ---------------------------------
# Match every traffic row
# with the closest weather row
# ---------------------------------

for traffic in TrafficData.objects.select_related("location").all():

    weather_data = WeatherData.objects.filter(
        location=traffic.location
    )

    # Skip if this location has no weather data
    if not weather_data.exists():
        continue

    # Find weather observation closest in time
    closest_weather = min(
        weather_data,
        key=lambda w: abs(
            w.recorded_time - traffic.recorded_time
        )
    )

    # Calculate timestamp difference
    time_difference = abs(
        closest_weather.recorded_time -
        traffic.recorded_time
    )

    # Don't pair observations more than 10 minutes apart
    if time_difference > timedelta(minutes=10):
        continue

    # ---------------------------------
    # Add combined row
    # ---------------------------------

    rows.append({
        "location": traffic.location.location_name,

        "recorded_time": traffic.recorded_time,

        # Traffic information
        "current_speed": traffic.current_speed,
        "free_flow_speed": traffic.free_flow_speed,
        "congestion_ratio": traffic.congestion_ratio,
        "confidence": traffic.confidence,

        # Location information
        "speed_limit": traffic.location.speed_limit,
        "road_type": traffic.location.road_type,
        "lanes": traffic.location.lanes,
        "aadt": traffic.location.aadt,
        "historical_crashes_2yr":
            traffic.location.historical_crashes_2yr,

        # Weather information
        "temperature": closest_weather.temperature,
        "humidity": closest_weather.humidity,
        "precipitation": closest_weather.precipitation,
        "wind_speed": closest_weather.wind_speed,
    })


# ---------------------------------
# Create DataFrame
# ---------------------------------

df = pd.DataFrame(rows)


# ---------------------------------
# Convert timestamp into ML features
# ---------------------------------

if not df.empty:

    df["recorded_time"] = pd.to_datetime(
        df["recorded_time"]
    )

    # Hour of day
    df["hour"] = df["recorded_time"].dt.hour

    # Day of week
    # Monday = 0
    # Sunday = 6
    df["day_of_week"] = (
        df["recorded_time"].dt.dayofweek
    )

    # Weekend indicator
    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)


# ---------------------------------
# Save training dataset
# ---------------------------------

df.to_csv(
    "ml/traffic_training_data.csv",
    index=False
)


# ---------------------------------
# Display information
# ---------------------------------

print("Dataset created!")
print()

print("Rows:", len(df))
print()

print("Columns:")
print(df.columns.tolist())
print()

print("First 5 rows:")
print(df.head())