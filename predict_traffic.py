import os
import django
import joblib
from datetime import datetime
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrafficAI.settings")
django.setup()

from predictions.models import Location, TrafficPrediction, WeatherPrediction


models = {"current_speed": joblib.load("ml/traffic_current_speed_model.pkl"),
          "free_flow_speed": joblib.load("ml/traffic_free_flow_speed_model.pkl"),
          "temperature":  joblib.load("ml/traffic_temperature_model.pkl"),
          "humidity": joblib.load("ml/traffic_humidity_model.pkl"),
          "precipitation": joblib.load("ml/traffic_precipitation_model.pkl"),
          "wind_speed": joblib.load("ml/traffic_wind_speed_model.pkl")
}

print("Models Loaded Successfully!")

now = timezone.now()
hour = now.hour
day_of_week = now.weekday()
is_weekend = 1 if day_of_week >= 5 else 0

locations = Location.objects.all()

print(f"Generating predictions for {locations.count()} locations at {now}...")

for location in locations:
    # Get latest weather from database (from last API call)
    from predictions.models import WeatherData
    latest_weather = WeatherData.objects.filter(location=location).order_by("-recorded_time").first()

    features = {
        "location": location.location_name,
        "road_type": location.road_type,
        "speed_limit": location.speed_limit,
        "lanes": location.lanes,
        "aadt": location.aadt,
        "historical_crashes_2yr": location.historical_crashes_2yr,
        "hour": hour,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "temperature": latest_weather.temperature,
        "humidity": latest_weather.humidity,
        "precipitation": latest_weather.precipitation,
        "wind_speed": latest_weather.wind_speed,
    }

    import pandas as pd

    features_df = pd.DataFrame([features])

    current_speed_pred = models["current_speed"].predict(features_df)[0]
    free_flow_speed_pred = models["free_flow_speed"].predict(features_df)[0]
    temperature_pred = models["temperature"].predict(features_df)[0]
    humidity_pred = models["humidity"].predict(features_df)[0]
    precipitation_pred = models["precipitation"].predict(features_df)[0]
    wind_speed_pred = models["wind_speed"].predict(features_df)[0]

    congestion_ratio = current_speed_pred / free_flow_speed_pred if free_flow_speed_pred > 0 else 0

    TrafficPrediction.objects.create(
        location=location,
        predicted_time=now,
        current_speed=current_speed_pred,
        free_flow_speed=free_flow_speed_pred,
        congestion_ratio=congestion_ratio,
    )
    
    # Save weather predictions
    WeatherPrediction.objects.create(
        location=location,
        predicted_time=now,
        temperature=temperature_pred,
        humidity=humidity_pred,
        precipitation=precipitation_pred,
        wind_speed=wind_speed_pred,
    )

print("Predictions saved!")