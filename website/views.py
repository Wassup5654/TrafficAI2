from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone

from datetime import timedelta

from predictions.models import (
    Location,
    TrafficData,
    WeatherData,
    TrafficPrediction,
)


# Home page
def home(request):
    return render(request, "website/home.html", context={})


# Login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            next_url = (
                request.POST.get("next")
                or request.GET.get("next")
                or "home"
            )

            return redirect(next_url)

        else:
            return render(
                request,
                "website/login.html",
                {
                    "error_message": "Invalid login credentials"
                }
            )

    return render(request, "website/login.html")


# Register
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")

        if password != confirm_password:
            return render(
                request,
                "website/register.html",
                {
                    "error": "Passwords do not match."
                }
            )

        if User.objects.filter(username=username).exists():
            return render(
                request,
                "website/register.html",
                {
                    "error": "That username is already taken."
                }
            )

        User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=fname,
            last_name=lname
        )

        return redirect("login")

    return render(request, "website/register.html")


# Dashboard

def dashboard(request):
    locations = Location.objects.all()

    traffic_data = (
        TrafficData.objects
        .all()
        .order_by("-recorded_time")[:100]
    )

    location_data = [
        {
            "name": location.location_name,
            "lat": location.latitude,
            "lon": location.longitude,
            "road": location.road_type,
            "crashes": location.historical_crashes_2yr,
            "aadt": location.aadt,
        }
        for location in locations
    ]

    return render(
        request,
        "website/dashboard.html",
        {
            "locations": locations,
            "location_data": location_data,
            "traffic_data": traffic_data,
        }
    )


# Location detail

def location_detail(request, location_id):

    # Only show the last 24 hours on the graph
    twenty_four_hours_ago = (
        timezone.now() - timedelta(hours=24)
    )

    location = get_object_or_404(
        Location,
        id=location_id
    )

    # Traffic observations from the last 24 hours
    traffic_data = (
        TrafficData.objects
        .filter(
            location=location,
            recorded_time__gte=twenty_four_hours_ago
        )
        .order_by("recorded_time")
    )

    # Most recent weather observations
    weather_data = (
        WeatherData.objects
        .filter(location=location)
        .order_by("-recorded_time")[:10]
    )

    # AI predictions from the last 24 hours
    prediction_data = (
        TrafficPrediction.objects
        .filter(
            location=location,
            predicted_time__gte=twenty_four_hours_ago
        )
        .order_by("predicted_time")
    )

    # Combine traffic and closest weather data
    combined_data = []

    for traffic in traffic_data[:10]:

        weather = None
        smallest_difference = float("inf")

        for w in weather_data:

            time_diff = abs(
                (
                    traffic.recorded_time
                    - w.recorded_time
                ).total_seconds()
            )

            if time_diff < smallest_difference:
                smallest_difference = time_diff
                weather = w

        # Only use weather within 5 minutes
        if smallest_difference > 300:
            weather = None

        combined_data.append(
            {
                "traffic": traffic,
                "weather": weather,
            }
        )

    # --------------------------------------------------
    # SPEED GRAPH
    # --------------------------------------------------

    # Time labels for the graph
    # Convert UTC timestamps to local Eastern time
    chart_labels = [
        timezone.localtime(
            traffic.recorded_time
        ).strftime("%m/%d %H:%M")
        for traffic in traffic_data
    ]

    # Actual traffic speeds from TomTom
    chart_speeds = [
        traffic.current_speed
        for traffic in traffic_data
    ]

    # Create a lookup table:
    #
    # prediction timestamp -> predicted speed
    #
    # predict_traffic.py uses:
    # predicted_time = traffic.recorded_time
    #
    # so the timestamps should line up.
    prediction_lookup = {
    prediction.predicted_time: prediction.current_speed
    for prediction in prediction_data
    }
    if traffic_data:

        for prediction in prediction_data:

            closest_traffic = min(
            traffic_data,
            key=lambda traffic: abs(
                traffic.recorded_time -
                prediction.predicted_time
            )
        )

        time_difference = abs(
            closest_traffic.recorded_time -
            prediction.predicted_time
        ).total_seconds()

        if time_difference <= 300:
            prediction_lookup[
                closest_traffic.recorded_time
            ] = prediction.current_speed


    chart_predictions = [
    prediction_lookup.get(
        traffic.recorded_time
    )
    for traffic in traffic_data
]

    # --------------------------------------------------
    # SEND DATA TO TEMPLATE
    # --------------------------------------------------

    return render(
        request,
        "website/location_detail.html",
        {
            "location": location,
            "combined_data": combined_data,

            # Graph data
            "chart_labels": chart_labels,
            "chart_speeds": chart_speeds,
            "chart_predictions": chart_predictions,
        },
    )