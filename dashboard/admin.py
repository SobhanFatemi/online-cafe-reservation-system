from django.contrib import admin
from django.contrib import admin, messages
from common.admin import BaseAdmin
from .models import CafeSetting


@admin.register(CafeSetting)
class CafeSettingAdmin(BaseAdmin):
    list_display = (
        "cancel_window_hours",
        "allow_user_cancel",
        "allow_admin_late_cancel",
        "reservations_enabled",
        "slot_duration_minutes",
        "auto_generate_days_ahead",
    )
