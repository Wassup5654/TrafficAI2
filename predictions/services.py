from predictions.models import ApiCallLog, Location, TrafficData, WeatherData
from predictions.traffic_api import get_traffic_data
from predictions.weather_api import get_current_weather
import time
from django.utils import timezone



MAX_TRAFFIC_RECORDS = 10000

DAILY_CALL_LIMIT = 999

def can_make_api_call():
    today = timezone.localdate()
    log, created = ApiCallLog.objects.get_or_create(date=today)
    return log.call_count < DAILY_CALL_LIMIT

def increment_api_call_count():
    today = timezone.localdate()
    log, created = ApiCallLog.objects.get_or_create(date=today)
    log.call_count += 1
    log.save()

def update_location_traffic(location, timestamp):
    if not can_make_api_call():
        print("Daily HERE quota reached. Skipping:", location.location_name)
        return

    

    traffic = get_traffic_data(
        location.latitude,
        location.longitude
    )

    increment_api_call_count()

    if traffic is None:
        print("No traffic data:", location.location_name)
        return

    TrafficData.objects.create(
        location=location,
        current_speed=traffic["current_speed"],
        free_flow_speed=traffic["free_flow_speed"],
        congestion_ratio=traffic["congestion_ratio"],
        confidence=traffic["confidence"],
        source=traffic["source"],
        recorded_time=timestamp
    )

def update_location_weather(location, timestamp):

    weather = get_current_weather(
        location.latitude,
        location.longitude
    )

    if weather is None:
        print("No weather data:", location.location_name)
        return

    WeatherData.objects.create(
        location=location,
        recorded_time=timestamp,
        temperature=weather["temperature"],
        humidity=weather["humidity"],
        precipitation=weather["precipitation"],
        wind_speed=weather["wind_speed"],
        cloud_cover=weather["cloud_cover"]

    )

def update_all_locations():
    
    locations = Location.objects.all()

    for location in locations:
        print("Updating:", location.location_name)
        timestamp = timezone.now()
        try:
            update_location_traffic(location, timestamp)
        except Exception as e:
            print("FAILED:", location.location_name, e)
            print(type(e).__name__, e)
            continue

        try:
            update_location_weather(location, timestamp = timezone.now())
        except Exception as e:
            print("WEATHER FAILED:", location.location_name, type(e).__name__, e)

        time.sleep(1)

   