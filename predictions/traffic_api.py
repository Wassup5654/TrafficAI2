import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()


def get_traffic_data(latitude, longitude):

    api_key = os.getenv("HERE_API_KEY")

    here_url = "https://data.traffic.hereapi.com/v7/flow"

    response = requests.get(
        here_url,
        params={
            "apiKey": api_key,
            "locationReferencing": "shape",
            "in": f"circle:{latitude},{longitude};r=2000"
        }
    )

    # Handle rate limits
    if response.status_code == 429:
        print("HERE rate limit reached. Waiting...")
        time.sleep(5)
        return get_traffic_data(latitude, longitude)

    data = response.json()

    # Handle HERE errors
    if "results" not in data or len(data["results"]) == 0:
        print("HERE failed for coordinates:")
        print(latitude, longitude)
        print(data)
        return None



    for result in data["results"] :
        flow = result.get("currentFlow", {})

        current_speed = flow.get("speed")
        free_flow_speed = flow.get("freeFlow")

        if (
            current_speed is not None
            and free_flow_speed is not None
            and flow.get("traversability") != "closed"
        ):
            break

        subsegments = flow.get("subSegments", [])

        usable_subsegments = []

        for subsegment in subsegments:

            if (
                subsegment.get("traversability") == "open"
                and subsegment.get("speed") is not None
                and subsegment.get("freeFlow") is not None
            ):
                usable_subsegments.append(subsegment)

        if not usable_subsegments:
            continue

        flow = max(
            usable_subsegments,
            key=lambda segment: segment.get("length", 0)
        )

        current_speed = flow["speed"]
        free_flow_speed = flow["freeFlow"]

        break

    else:
        print("HERE returned no usable traffic flow for coordinates:")
        print(latitude, longitude)
        return None
    # Convert m/s to mph (HERE returns speed in meters/second by default)
    current_speed *= 2.23694
    free_flow_speed *= 2.23694

    # Prevent division errors
    if free_flow_speed == 0:
        congestion_ratio = 0
    else:
        congestion_ratio = current_speed / free_flow_speed

    return {
        "current_speed": current_speed,
        "free_flow_speed": free_flow_speed,
        "congestion_ratio": congestion_ratio,
        "confidence": flow.get("jamFactor", 0),  # closest HERE equivalent to TomTom's confidence
        "source": "HERE"
    }