from django.db import models

class Type(models.TextChoices):
    PERCENT = "PER", "Percent",
    FIXED = "FIX", "Fixed amount",