from django.contrib import admin

# Register your models here.
from .models import Location, TrafficData, WeatherData, TrafficPrediction, WeatherPrediction

admin.site.register(Location)


@admin.register(TrafficData)
class TrafficDataAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "current_speed",
        "free_flow_speed",
        "congestion_ratio",
        "confidence",
        "recorded_time",
    )

    ordering = ("-recorded_time",)





@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):

    list_display = (
        "location",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "recorded_time",
    )

    ordering = ("-recorded_time",)

@admin.register(TrafficPrediction)
class TrafficPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "current_speed",
        "free_flow_speed",
        "congestion_ratio",
        "predicted_time",
        "created_at",
    )
    ordering = ("-predicted_time",)


@admin.register(WeatherPrediction)
class WeatherPredictionAdmin(admin.ModelAdmin):
    list_display = (
        "location",
        "temperature",
        "humidity",
        "precipitation",
        "wind_speed",
        "predicted_time",
        "created_at",
    )
    ordering = ("-predicted_time",)