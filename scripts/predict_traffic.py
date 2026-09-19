import os
import sys
import django
import joblib
import pandas as pd

from datetime import timedelta
from django.utils import timezone


# ============================================================
# DJANGO PROJECT SETUP
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


# ============================================================
# IMPORT MODELS
# ============================================================

from predictions.models import (
    Location,
    TrafficData,
    WeatherData,
    TrafficPrediction,
    WeatherPrediction,
)


# ============================================================
# LOAD ML MODELS
# ============================================================

models = {

    "next_speed": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_next_speed_model.pkl"
        )
    ),

    "free_flow_speed": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_free_flow_speed_model.pkl"
        )
    ),

    "temperature": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_temperature_model.pkl"
        )
    ),

    "humidity": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_humidity_model.pkl"
        )
    ),

    "precipitation": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_precipitation_model.pkl"
        )
    ),

    "wind_speed": joblib.load(
        os.path.join(
            PROJECT_ROOT,
            "ml",
            "traffic_wind_speed_model.pkl"
        )
    ),
}


print()
print("Models Loaded Successfully!")


# ============================================================
# CURRENT TIME
# ============================================================

now = timezone.now()

prediction_time = now + timedelta(
    minutes=2
)

day_of_week = now.weekday()

is_weekend = (
    1 if day_of_week >= 5
    else 0
)


# ============================================================
# GET LOCATIONS
# ============================================================

locations = Location.objects.all()


print()
print(
    f"Generating recursive 2-minute forecasts "
    f"for {locations.count()} locations..."
)

print(
    f"Current time: "
    f"{timezone.localtime(now).strftime('%Y-%m-%d %I:%M:%S %p')}"
)

print(
    f"Forecast time: "
    f"{timezone.localtime(prediction_time).strftime('%Y-%m-%d %I:%M:%S %p')}"
)


# ============================================================
# PROCESS EACH LOCATION
# ============================================================

predictions_created = 0
weather_predictions_created = 0


for location in locations:

    print()
    print("=" * 60)
    print(
        f"Processing: "
        f"{location.location_name}"
    )
    print("=" * 60)


    # ========================================================
    # GET LATEST REAL TRAFFIC DATA
    # ========================================================

    latest_traffic = (
        TrafficData.objects
        .filter(
            location=location
        )
        .order_by(
            "-recorded_time"
        )
        .first()
    )


    if latest_traffic is None:

        print(
            "Skipping: no traffic data."
        )

        continue


    # ========================================================
    # GET LATEST WEATHER
    # ========================================================

    latest_weather = (
        WeatherData.objects
        .filter(
            location=location
        )
        .order_by(
            "-recorded_time"
        )
        .first()
    )


    if latest_weather is None:

        print(
            "Skipping: no weather data."
        )

        continue


    # ========================================================
    # DETERMINE PREVIOUS SPEED
    # ========================================================
    #
    # If a previous prediction already exists after the
    # latest real API observation, use that prediction.
    #
    # Otherwise, start the recursive chain using the
    # latest real traffic speed.
    # ========================================================

    previous_prediction = (
        TrafficPrediction.objects
        .filter(
            location=location,
            predicted_time__gt=
                latest_traffic.recorded_time
        )
        .order_by(
            "-predicted_time"
        )
        .first()
    )


    if previous_prediction is not None:

        previous_speed = (
            previous_prediction.current_speed
        )

        print(
            f"Using previous prediction: "
            f"{previous_speed:.2f} mph"
        )

    else:

        previous_speed = (
            latest_traffic.current_speed
        )

        print(
            f"Starting with real speed: "
            f"{previous_speed:.2f} mph"
        )


    # ========================================================
    # BUILD FEATURES
    # ========================================================

    features = {

        "location":
            location.location_name,

        "road_type":
            location.road_type,

        "speed_limit":
            location.speed_limit,

        "lanes":
            location.lanes,

        "aadt":
            location.aadt,

        "historical_crashes_2yr":
            location.historical_crashes_2yr,

        "hour":
            now.hour,

        "day_of_week":
            day_of_week,

        "is_weekend":
            is_weekend,

        # THIS IS THE IMPORTANT PART
        "previous_speed":
            previous_speed,

        "temperature":
            latest_weather.temperature,

        "humidity":
            latest_weather.humidity,

        "precipitation":
            latest_weather.precipitation,

        "wind_speed":
            latest_weather.wind_speed,
    }


    features_df = pd.DataFrame(
        [features]
    )


    # ========================================================
    # PREDICT NEXT SPEED
    # ========================================================

    next_speed_pred = models[
        "next_speed"
    ].predict(
        features_df
    )[0]


    # ========================================================
    # PREDICT FREE-FLOW SPEED
    # ========================================================

    free_flow_speed_pred = models[
        "free_flow_speed"
    ].predict(
        features_df
    )[0]


    # ========================================================
    # PREDICT WEATHER
    # ========================================================

    temperature_pred = models[
        "temperature"
    ].predict(
        features_df
    )[0]

    humidity_pred = models[
        "humidity"
    ].predict(
        features_df
    )[0]

    precipitation_pred = models[
        "precipitation"
    ].predict(
        features_df
    )[0]

    wind_speed_pred = models[
        "wind_speed"
    ].predict(
        features_df
    )[0]


    # ========================================================
    # CALCULATE CONGESTION
    # ========================================================

    if free_flow_speed_pred > 0:

        congestion_ratio = (
            next_speed_pred /
            free_flow_speed_pred
        )

    else:

        congestion_ratio = 0


    # ========================================================
    # SAVE TRAFFIC PREDICTION
    # ========================================================

    TrafficPrediction.objects.create(

        location=location,

        predicted_time=prediction_time,

        current_speed=next_speed_pred,

        free_flow_speed=
            free_flow_speed_pred,

        congestion_ratio=
            congestion_ratio,
    )


    predictions_created += 1


    # ========================================================
    # SAVE WEATHER PREDICTION
    # ========================================================

    WeatherPrediction.objects.create(

        location=location,

        predicted_time=prediction_time,

        temperature=
            temperature_pred,

        humidity=
            humidity_pred,

        precipitation=
            precipitation_pred,

        wind_speed=
            wind_speed_pred,
    )


    weather_predictions_created += 1


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print()
    print(
        f"Real speed: "
        f"{latest_traffic.current_speed:.2f} mph"
    )

    print(
        f"Previous speed used by model: "
        f"{previous_speed:.2f} mph"
    )

    print(
        f"Predicted next speed: "
        f"{next_speed_pred:.2f} mph"
    )

    print(
        f"Free-flow speed: "
        f"{free_flow_speed_pred:.2f} mph"
    )

    print(
        f"Congestion ratio: "
        f"{congestion_ratio:.2f}"
    )

    print(
        f"Forecast time: "
        f"{timezone.localtime(prediction_time).strftime('%I:%M:%S %p')}"
    )


# ============================================================
# FINISHED
# ============================================================

print()
print("=" * 60)
print("RECURSIVE PREDICTION RUN COMPLETED")
print("=" * 60)

print(
    f"Traffic predictions created: "
    f"{predictions_created}"
)

print(
    f"Weather predictions created: "
    f"{weather_predictions_created}"
)

print(
    f"Forecast time: "
    f"{timezone.localtime(prediction_time).strftime('%I:%M:%S %p')}"
)

print("=" * 60)