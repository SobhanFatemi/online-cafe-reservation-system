from django.contrib import admin
from common.admin import BaseAdmin
from .models import Reservation, ReservationFood, Review, ReviewReply


class ReservationFoodInline(admin.TabularInline):
    model = ReservationFood
    extra = 0
    autocomplete_fields = ("food_item",)

@admin.register(Reservation)
class ReservationAdmin(BaseAdmin):
    list_display = (
        "id",
        "user",
        "table",
        "date",
        "number_of_people",
        "status",
        "attendance_status",
        "total_price",
    )

    list_filter = (
        "status",
        "attendance_status",
        "date",
        "time_slot",
        "table",
    )

    search_fields = (
        "user__username",
        "user__email",
        "table__table_number",
    )

    list_select_related = (
        "user",
        "table",
        "time_slot",
    )

    inlines = [ReservationFoodInline]
    date_hierarchy = "date"
    ordering = ("-created_at",)

@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = (
        "id",
        "user",
        "reservation",
        "rating",
        "created_at",
    )

    list_filter = ("rating", "created_at")
    search_fields = (
        "user__username",
        "reservation__id",
        "comment",
    )

    list_select_related = ("user", "reservation")

@admin.register(ReviewReply)
class ReviewReplyAdmin(BaseAdmin):
    list_display = (
        "id",
        "admin",
        "review",
        "created_at",
    )

    search_fields = (
        "admin__username",
        "review__id",
        "reply_text",
    )

    list_select_related = ("admin", "review")