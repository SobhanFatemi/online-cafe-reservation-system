from django.db import models

class DayofWeek(models.TextChoices):
    MONDAY = "MON", "Monday"
    TUESDAY = "TUE", "Tuesday"
    WEDNESDAY = "WED", "Wednesday"
    THURSDAY = "THU", "Thursday"
    FRIDAY = "FRI", "Friday"
    SATURDAY = "SAT", "Saturday"
    SUNDAY = "SUN", "Sunday"