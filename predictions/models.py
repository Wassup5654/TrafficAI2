from django.db import models

# Create your models here.



class Location(models.Model):
    location_name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed_limit = models.IntegerField(default = 25)
    road_type = models.CharField(max_length=50)

    lanes = models.IntegerField(default=2)
    aadt = models.IntegerField(default=0)
    rush_hour = models.CharField(max_length=50, default='8:00 AM - 9:00 AM')
    historical_crashes_2yr = models.IntegerField(default=0)
   

   

    

    def __str__(self):
        return self.location_name


class TrafficData(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE
    )

    recorded_time = models.DateTimeField()
    

    confidence = models.FloatField(null=True, blank=True)

    current_speed = models.FloatField(null=True, blank=True)

    free_flow_speed = models.FloatField(null=True, blank=True)

    congestion_ratio = models.FloatField(null=True, blank=True)

    source = models.CharField(max_length=50, default='TomTom')
    def __str__(self):
        return self.location.location_name

    def __str__(self):
        return self.location.location_name

class WeatherData(models.Model):
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE
    )

    temperature = models.FloatField()
    humidity = models.FloatField()
    precipitation = models.FloatField()
    wind_speed = models.FloatField()
    cloud_cover = models.FloatField()

    recorded_time = models.DateTimeField()

    def __str__(self):
        return f"{self.location.location_name} - {self.recorded_time}"

class ApiCallLog(models.Model):
    date = models.DateField()
    call_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.date}: {self.call_count} calls"


class TrafficPrediction(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    predicted_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    current_speed = models.FloatField(null=True, blank=True)
    free_flow_speed = models.FloatField(null=True, blank=True)
    congestion_ratio = models.FloatField(null=True, blank=True)

class WeatherPrediction(models.Model):
    location = models.ForeignKey(Location, on_delete = models.CASCADE)
    predicted_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    temperature = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)