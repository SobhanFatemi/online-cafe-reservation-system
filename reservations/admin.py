from django.contrib import admin
from common.admin import BaseAdmin
from .models import Reservation, ReservationFood, Comment, Reply


class ReservationFoodInline(admin.TabularInline):
    model = ReservationFood
    extra = 0
    exclude = "is_deleted",
    autocomplete_fields = ("food_item",)


@admin.register(Reservation)
class ReservationAdmin(BaseAdmin):
    list_display = (
        "id",
        "user",
        "time_slot__table",
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
        "time_slot__table",
    )

    search_fields = (
        "user__username",
        "user__email",
        "time_slot__table__table_number",
    )

    list_select_related = (
        "user",
        "time_slot__table",
    )

    inlines = [ReservationFoodInline]
    date_hierarchy = "date"
    ordering = ("-created_at",)

@admin.register(Comment)
class CommentAdmin(BaseAdmin):
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

@admin.register(Reply)
class ReplyAdmin(BaseAdmin):
    list_display = (
        "id",
        "user",
        "comment",
        "created_at",
    )

    search_fields = (
        "user__username",
        "comment__id",
        "reply",
    )

    list_select_related = ("user", "comment")