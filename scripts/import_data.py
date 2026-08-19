import os
import sys
import django
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Connect script to Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TrafficAI.settings")
django.setup()

from predictions.models import Location

with open('data/data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        location = Location.objects.update_or_create(
            location_name=row["location_name"],
            defaults={
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "speed_limit": int(row["speed_limit"]),
                "road_type": row["road_type"],
                "lanes": int(row["lanes"]),
                "aadt": int(row["aadt"]),
                "rush_hour": row["rush_hour"],
                "historical_crashes_2yr": int(row["historical_crashes_2yr"])
            }
        )


if __name__ == "__main__":
    print("Importing locations from CSV...")
