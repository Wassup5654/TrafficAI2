import requests


def get_current_weather(latitude, longitude):
    """
    Gets current weather from Open-Meteo Forecast API
    """

    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}"
        f"&longitude={longitude}"
        "&current="
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
        print("Weather API failed:", response.status_code)
        return None

    data = response.json()
    current = data.get("current")

    if current is None:
        print("No current weather data returned")
        return None

    return {
        "temperature": current.get("temperature_2m"),
        "humidity": current.get("relative_humidity_2m"),
        "precipitation": current.get("precipitation"),
        "wind_speed": current.get("wind_speed_10m"),
        "cloud_cover": current.get("cloud_cover"),
    }