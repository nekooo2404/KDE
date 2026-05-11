from django.db import models

class LocationTerm(models.Model):
    term = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    density = models.FloatField(default=0.5)
    city = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.term} -> {self.city}"