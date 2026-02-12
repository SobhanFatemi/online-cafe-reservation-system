from django.db import models


class CafeSetting(models.Model):
    cancel_window_hours = models.PositiveIntegerField(
        default=1
    )

    allow_user_cancel = models.BooleanField(
        default=True
    )
    allow_admin_late_cancel = models.BooleanField(
        default=True
    )

    reservations_enabled = models.BooleanField(
        default=True
    )

    slot_duration_minutes = models.PositiveIntegerField(
        default=120
    )

    auto_generate_days_ahead = models.PositiveIntegerField(
        default=7
    )

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Cafe System Settings"