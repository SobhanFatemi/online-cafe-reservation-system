from django.db import models

class Rating(models.IntegerChoices):
    ONE = 1, "⭐"
    TWO = 2, "⭐⭐"
    THREE = 3, "⭐⭐⭐"
    FOUR = 4, "⭐⭐⭐⭐"
    FIVE = 5, "⭐⭐⭐⭐⭐"

class Status(models.TextChoices):
    PENDING = "PEN", "Pending"
    CONFIRMED = "CON", "Confirmed"
    CANCELLED = "CAN", "Canceled"
    COMPELETED = "COM", "Compeleted"

class AttendanceStatus(models.TextChoices):
    UNKNOWN = "UNK", "Unknown"
    PRESENT = "PRE", "Present"
    ABSENT = "ABS", "Absent"