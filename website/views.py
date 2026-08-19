
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, request
from django.contrib.auth.models import User
from predictions.models import Location, TrafficData, WeatherData
from django.shortcuts import get_object_or_404
# Create your views here.

def home(request):
    return render(request, 'website/home.html', context={})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)  # Redirect to a success page.
        else:
            # Return an 'invalid login' error message.
            return render(request, 'website/login.html', {'error_message': 'Invalid login credentials'})
    else:
        return render(request, 'website/login.html')




def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')

        if password != confirm_password:
            return render(request, 'website/register.html', {'error': 'Passwords do not match.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'website/register.html', {'error': 'That username is already taken.'})

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=fname,
            last_name=lname
        )

        return redirect('login')

    return render(request, 'website/register.html')

@login_required
def dashboard(request):
    locations = Location.objects.all()

    traffic_data = TrafficData.objects.all().order_by("-recorded_time")[:100]


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

    return render( request, "website/dashboard.html", {"locations": locations, "location_data": location_data, "traffic_data": traffic_data})

@login_required
def location_detail(request, location_id):
    location = get_object_or_404(Location, id=location_id)

    traffic_data = TrafficData.objects.filter(
        location=location
    ).order_by("-recorded_time")[:10]

    weather_data = WeatherData.objects.filter(
        location=location
    ).order_by("-recorded_time")[:10]

    combined_data = []

    for traffic in traffic_data:
        weather = None
        smallest_difference = float("inf")

        for w in weather_data:
            time_diff = abs(
                (traffic.recorded_time - w.recorded_time).total_seconds()
            )

            if time_diff < smallest_difference:
                smallest_difference = time_diff
                weather = w

        # Only use weather if it is within 5 minutes
        if smallest_difference > 300:
            weather = None

        combined_data.append({
            "traffic": traffic,
            "weather": weather,
        })

    return render(
        request,
        "website/location_detail.html",
        {
            "location": location,
            "combined_data": combined_data,
        },
    )
