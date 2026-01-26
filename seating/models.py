from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date

class DayofWeek(models.TextChoices):
    MONDAY = "MON", "Monday"
    TUESDAY = "TUE", "Tuesday"
    WEDNESDAY = "WED", "Wednesday"
    THURSDAY = "THU", "Thursday"
    FRIDAY = "FRI", "Friday"
    SATURDAY = "SAT", "Saturday"
    SUNDAY = "SUN", "Sunday"


class CafeTable(models.Model):
    table_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        verbose_name="Table Number"
    )

    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Capacity"
    )

    price_per_person = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Price (Per Person)"
    )

    is_active = models.BooleanField(
        verbose_name="Is Active"
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    def __str__(self):
        return f"Table #{self.table_number}"

class TimeSlot(models.Model):
    start_time = models.TimeField(
        verbose_name="Start Time"
    )

    end_time = models.TimeField(
        verbose_name="End Time"
    )

    duration_minutes = models.PositiveIntegerField(
        verbose_name="Duration (In Minutes)",
        editable=False,
    )

    def clean(self):
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)

            diff = end - start
            if diff.total_seconds() <= 0:
                raise ValidationError({
                   "end_time": "End Time must be after Start Time!"
                })
            
    def save(self, *args, **kwargs):
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)

            self.duration_minutes  =int((end - start).total_seconds / 60)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Time Slot: {self.duration_minutes} Minutes"

class WorkingHour(models.Model):
    start_time = models.TimeField(
        verbose_name="Start Time"
    )

    end_time = models.TimeField(
        verbose_name="End Time"
    )

    day_of_week = models.CharField(
        unique=True,
        max_length=3,
        verbose_name="Day of Week",
        choices=DayofWeek.choices,
    )

    def __str__(self):
        return self.get_day_of_week_display()