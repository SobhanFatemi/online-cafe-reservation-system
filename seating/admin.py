from django.contrib import admin
from common.admin import BaseAdmin
from .models import CafeTable, TimeSlot, WorkingHour


@admin.register(CafeTable)
class CafeTableAdmin(BaseAdmin):
    list_display = (
        "id",
        "table_number",
        "capacity",
        "price_per_person",
        "is_active",
    )
    search_fields = ("table_number",)
    list_filter = ("is_active", "capacity")
    ordering = ("table_number",)


@admin.register(TimeSlot)
class TimeSlotAdmin(BaseAdmin):
    list_display = ("id", "start_time", "end_time", "duration_minutes")
    ordering = ("start_time",)


@admin.register(WorkingHour)
class WorkingHourAdmin(BaseAdmin):
    list_display = ("day_of_week", "start_time", "end_time")
    list_filter = ("day_of_week",)
    ordering = ("day_of_week",)
