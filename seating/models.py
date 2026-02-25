from django.db import models
from common.models import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date
from .choices import DayofWeek
from django.utils import timezone

class CafeTable(BaseModel):
    table_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        unique=True,
        verbose_name="Table Number"
    )

    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name="Capacity"
    )

    price_per_person = models.DecimalField(
        validators=[MinValueValidator(0)],
        max_digits=10,
        decimal_places=2,
        verbose_name="Price (Per Person)"
    )

    is_active = models.BooleanField(
        verbose_name="Is Active",
        default=True,
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
        return f"Table {self.table_number}"

class TimeSlot(BaseModel):
    table = models.ForeignKey(
        "CafeTable",
        on_delete=models.CASCADE,
        related_name="time_slots"
    )

    date = models.DateField(
        verbose_name="Date",
    )

    start_time = models.TimeField(
        verbose_name="Start Time"
    )
    end_time = models.TimeField(
        verbose_name="End Time"
    )

    duration_minutes = models.PositiveIntegerField(
        editable=False
    )

    is_active = models.BooleanField(
        verbose_name="Is Active",
        default=True,
    )

    note = models.CharField(
        verbose_name="Note",
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ("table", "date", "start_time")
        ordering = ["date", "start_time"]

    def clean(self):
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)

            if end <= start:
                raise ValidationError({
                    "end_time": "End time must be after start time."
                })

            self.duration_minutes = int(
                (end - start).total_seconds() / 60
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.start_time} - {self.end_time}"

class WorkingHour(BaseModel):
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

    is_closed = models.BooleanField(
        verbose_name="Is Closed",
        default=False
    )

    def __str__(self):
        return self.get_day_of_week_display()