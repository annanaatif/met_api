from django.db import models

class Region(models.Model):
    code = models.CharField(max_length=64, unique=True)  # e.g. "UK", "England_N", "Scotland"
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Parameter(models.TextChoices):
    TMAX = "Tmax", "Max temp"
    TMIN = "Tmin", "Min temp"
    TMEAN = "Tmean", "Mean temp"
    SUN = "Sun", "Sunshine"
    RAIN = "Rain", "Rainfall"
    RAINDAYS = "Raindays", "Rain days >=1.0mm"
    FROSTDAYS = "Frost", "Days of air frost"


class MonthlySeries(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="monthly_series")
    parameter = models.CharField(max_length=20, choices=Parameter.choices)
    year = models.IntegerField(db_index=True)
    month = models.PositiveSmallIntegerField()  # 1..12
    value = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("region", "parameter", "year", "month")
        indexes = [
            models.Index(fields=["region", "parameter", "year"]),
            models.Index(fields=["parameter", "year", "month"]),
        ]
        ordering = ["region", "parameter", "year", "month"]

    def __str__(self):
        return f"{self.region.code} {self.parameter} {self.year}-{self.month:02d}: {self.value}"
