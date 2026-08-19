import os
import sys
import math
import csv
import xml.etree.ElementTree as ET

import django

# --------------------------------------------------
# Connect to Django
# --------------------------------------------------

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "TrafficAI.settings"
)

django.setup()

from predictions.models import Location


# --------------------------------------------------
# File locations
# --------------------------------------------------

XML_FILE = "ml/trafficSensor_tmdd.xml"
OUTPUT_FILE = "ml/location_sensor_matches.csv"


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def clean_tag(tag):
    """
    Removes the XML namespace from a tag.

    Example:
    {http://...}vehicle-speed
    becomes:
    vehicle-speed
    """

    return tag.split("}")[-1]


def get_text(element, wanted_tag):
    """
    Finds the first element with the requested tag
    and returns its text.
    """

    for child in element.iter():

        if clean_tag(child.tag) == wanted_tag:

            if child.text:
                return child.text.strip()

    return None


def get_all_text(element, wanted_tag):
    """
    Gets every occurrence of a particular tag.
    """

    values = []

    for child in element.iter():

        if clean_tag(child.tag) == wanted_tag:

            if child.text:
                values.append(child.text.strip())

    return values


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates distance between two latitude/longitude
    coordinates.

    Returns distance in miles.
    """

    R = 3958.8  # Earth radius in miles

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)

    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.asin(math.sqrt(a))

    return R * c


def parse_coordinate(value):
    """
    Converts VDOT coordinates into normal decimals.

    Example:
    38301152 -> 38.301152
    -77503362 -> -77.503362
    """

    if value is None:
        return None

    value = value.strip()

    try:
        number = float(value)

        # VDOT data appears to use 6 decimal places
        if abs(number) > 180:
            number = number / 1_000_000

        return number

    except ValueError:
        return None


# --------------------------------------------------
# Read VDOT sensors
# --------------------------------------------------

print("Reading VDOT XML...")

tree = ET.parse(XML_FILE)
root = tree.getroot()

stations = []

for station in root.iter():

    if clean_tag(station.tag) != "station":
        continue

    latitude = parse_coordinate(
        get_text(station, "latitude")
    )

    longitude = parse_coordinate(
        get_text(station, "longitude")
    )

    if latitude is None or longitude is None:
        continue

    device_id = get_text(
        station,
        "device-id"
    )

    device_name = get_text(
        station,
        "device-name"
    )

    public_name = get_text(
        station,
        "device-public-name"
    )

    link_name = get_text(
        station,
        "link-name"
    )

    direction = get_text(
        station,
        "link-direction"
    )

    speeds = get_all_text(
        station,
        "vehicle-speed"
    )

    sample_periods = get_all_text(
        station,
        "sample-period"
    )

    timestamps = get_all_text(
        station,
        "iso-8601"
    )

    # Use the last reported speed in this station
    vehicle_speed = None

    if speeds:

        try:
            vehicle_speed = float(speeds[-1])

        except ValueError:
            pass

    sample_period = None

    if sample_periods:

        try:
            sample_period = int(
                sample_periods[-1]
            )

        except ValueError:
            pass

    timestamp = None

    if timestamps:
        timestamp = timestamps[-1]

    stations.append({

        "device_id": device_id,
        "device_name": device_name,
        "public_name": public_name,
        "link_name": link_name,
        "direction": direction,

        "latitude": latitude,
        "longitude": longitude,

        "vehicle_speed": vehicle_speed,
        "sample_period": sample_period,
        "timestamp": timestamp,
    })


print(
    f"VDOT sensors loaded: {len(stations)}"
)


# --------------------------------------------------
# Find nearest sensor for every TrafficAI location
# --------------------------------------------------

locations = Location.objects.all()

print(
    f"TrafficAI locations: {locations.count()}"
)

results = []


for location in locations:

    nearest_sensor = None
    nearest_distance = float("inf")

    for sensor in stations:

        distance = haversine(

            location.latitude,
            location.longitude,

            sensor["latitude"],
            sensor["longitude"]

        )

        if distance < nearest_distance:

            nearest_distance = distance
            nearest_sensor = sensor

    if nearest_sensor:

        results.append({

            "location_name":
                location.location_name,

            "location_latitude":
                location.latitude,

            "location_longitude":
                location.longitude,

            "sensor_device_id":
                nearest_sensor["device_id"],

            "sensor_name":
                nearest_sensor["device_name"],

            "sensor_public_name":
                nearest_sensor["public_name"],

            "link_name":
                nearest_sensor["link_name"],

            "direction":
                nearest_sensor["direction"],

            "sensor_latitude":
                nearest_sensor["latitude"],

            "sensor_longitude":
                nearest_sensor["longitude"],

            "distance_miles":
                round(nearest_distance, 3),

            "vehicle_speed":
                nearest_sensor["vehicle_speed"],

            "sample_period":
                nearest_sensor["sample_period"],

            "timestamp":
                nearest_sensor["timestamp"],
        })


# --------------------------------------------------
# Save results
# --------------------------------------------------

fieldnames = [

    "location_name",
    "location_latitude",
    "location_longitude",

    "sensor_device_id",
    "sensor_name",
    "sensor_public_name",

    "link_name",
    "direction",

    "sensor_latitude",
    "sensor_longitude",

    "distance_miles",

    "vehicle_speed",
    "sample_period",
    "timestamp",
]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)


# --------------------------------------------------
# Display results
# --------------------------------------------------

print()
print("Matching completed!")
print()

for result in results[:10]:

    print(
        f"{result['location_name']}"
    )

    print(
        f"  Nearest sensor: "
        f"{result['link_name']}"
    )

    print(
        f"  Distance: "
        f"{result['distance_miles']} miles"
    )

    print(
        f"  Speed: "
        f"{result['vehicle_speed']}"
    )

    print(
        f"  Timestamp: "
        f"{result['timestamp']}"
    )

    print()


print(
    f"Full results saved to: "
    f"{OUTPUT_FILE}"
)