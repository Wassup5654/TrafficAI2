import os
import django
import requests

from django.utils import timezone
from datetime import datetime


# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrafficAI.settings")
django.setup()


from predictions.models import TrafficData, WeatherData


def get_historical_weather(latitude, longitude, timestamp):
    """
    Gets historical weather from Open-Meteo Archive API
    """

    date = timestamp.strftime("%Y-%m-%d")

    url = (
        "https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={latitude}"
        f"&longitude={longitude}"
        f"&start_date={date}"
        f"&end_date={date}"
        "&hourly="
        "temperature_2m,"
        "relative_humidity_2m,"
        "precipitation,"
        "wind_speed_10m,"
        "cloud_cover"
        "&temperature_unit=fahrenheit"
        "&wind_speed_unit=mph"
    )


    response = requests.get(url)


    if response.status_code != 200:
        print(
            "Weather API failed:",
            response.status_code
        )
        return None


    data = response.json()

    return data["hourly"]



def find_closest_hour(weather_data, timestamp):
    """
    Finds closest hourly weather measurement
    """

    times = weather_data["time"]

    closest_index = min(
        range(len(times)),
        key=lambda i:
        abs(
            datetime.fromisoformat(times[i])
            - timestamp.replace(tzinfo=None)
        )
    )

    return closest_index



def backfill_weather():

    traffic_records = TrafficData.objects.all()

    total = traffic_records.count()

    print(
        f"Found {total} traffic records"
    )


    for index, traffic in enumerate(traffic_records):

        # Prevent duplicates
        exists = WeatherData.objects.filter(
            location=traffic.location,
            recorded_time=traffic.recorded_time
        ).exists()


        if exists:
            print(
                "Skipping existing:",
                traffic.recorded_time
            )
            continue


        weather = get_historical_weather(
            traffic.location.latitude,
            traffic.location.longitude,
            traffic.recorded_time
        )


        if weather is None:
            continue


        hour = find_closest_hour(
            weather,
            traffic.recorded_time
        )


        WeatherData.objects.create(

            location=traffic.location,

            temperature=
            weather["temperature_2m"][hour],

            humidity=
            weather["relative_humidity_2m"][hour],

            precipitation=
            weather["precipitation"][hour],

            wind_speed=
            weather["wind_speed_10m"][hour],

            cloud_cover=
            weather["cloud_cover"][hour],

            recorded_time=
            traffic.recorded_time
        )


        print(
            f"{index+1}/{total} completed"
        )


    print("Weather backfill finished!")



if __name__ == "__main__":
    backfill_weather()