from django.contrib import admin, messages
from common.admin import BaseAdmin
from .models import Reservation, ReservationFood, Comment, Reply
from .choices import Status, AttendanceStatus

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

    actions = (
        "confirm_reservation",
        "cancel_reservation",
        "compelete_reservation",
        "absent_reservation",
        "present_reservation",
    )

    @admin.action(description="Confirm selected reservations")
    def confirm_reservation(self, request, queryset):
        queryset.update(status=Status.CONFIRMED)
        self.message_user(request, "Reservation or Reservations are in Confirmed status now!", messages.SUCCESS)

    @admin.action(description="Cancel selected reservations")
    def cancel_reservation(self, request, queryset):
        queryset.update(status=Status.CANCELLED)
        self.message_user(request, "Reservation or Reservations are in Cancelled status now!", messages.SUCCESS)

    @admin.action(description="Compelete selected reservations")
    def compelete_reservation(self, request, queryset):
        queryset.update(status=Status.COMPELETED)
        self.message_user(request, "Reservation or Reservations are in Compeleted status now!", messages.SUCCESS)

    
    @admin.action(description="Absent selected reservations")
    def absent_reservation(self, request, queryset):
        queryset.update(attendance_status=AttendanceStatus.ABSENT)
        self.message_user(request, "Reservation's attendance status is Absent now!", messages.SUCCESS)
    
    @admin.action(description="Present selected reservations")
    def present_reservation(self, request, queryset):
        queryset.update(attendance_status=AttendanceStatus.PRESENT)
        self.message_user(request, "Reservation's attendance status is Present now!", messages.SUCCESS)

        

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