from django.db import models
from common.models import BaseModel
from seating.models import CafeTable, TimeSlot
from menu.models import FoodItem
from django.core.validators import MinValueValidator
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal
from .choices import Rating, Status, AttendanceStatus
from seating.models import WorkingHour
from seating.choices import DayofWeek
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class Reservation(BaseModel):
    user = models.ForeignKey(
        User,
        verbose_name="User",
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    time_slot = models.ForeignKey(
        TimeSlot,
        verbose_name="Time Slot",
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    date = models.DateField(
        verbose_name="Reservation Date"
    )

    status = models.CharField(
        max_length=3,
        verbose_name="Reservation Status",
        choices=Status.choices,
        default=Status.PENDING,
    )

    attendance_status = models.CharField(
        max_length=3,
        verbose_name="Attendance Status",
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.UNKNOWN,
    )

    number_of_people = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Number of People",
    )

    notes = models.TextField(
        max_length=256,
        verbose_name="Notes",
        blank=True
    )

    total_price = models.DecimalField(
        editable=False,
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    def calculate_total_price(self):
        food_total = (
            self.reservation_foods.aggregate(
                total=Sum("final_price")
            )["total"] or Decimal("0")
        )

        table_total = self.time_slot.table.price_per_person * self.number_of_people

        return food_total + table_total

    def update_total_price(self):
        self.total_price = self.calculate_total_price()
        self.save(update_fields=["total_price"])

    def get_start_datetime(self):
        return datetime.combine(
            self.date,
            self.time_slot.start_time,
        )

    def is_finished(self):
        if not self.date or not self.time_slot:
            return False
        
        start_dt = self.get_start_datetime()

        end_dt = start_dt + timedelta(minutes=self.time_slot.duration_minutes)

        return timezone.now() > timezone.make_aware(end_dt)
    
    def can_cancel(self):
        return timezone.make_aware(self.get_start_datetime()) - timezone.now() > timedelta(hours=2)

    def clean(self):
        super().clean()

        if self.time_slot:
            d = self.time_slot.duration_minutes

            if d < 30 or d > 180:
                raise ValidationError({
                    "time_slot": "Reservation duration must be between 30 minutes and 3 hours!"
                })
        
        if self.status == Status.CANCELED and not self.can_cancel():
            raise ValidationError({
                "status": "Reservation cannot be canceled less tha 2 hours before start!"
            })

        active_statuses = [
            Status.PENDING,
            Status.CONFIRMED,
        ]

        BUFFER = timedelta(minutes=15)

        conflict = Reservation.objects.filter(
            time_slot__table=self.time_slot.table,
            date=self.date,
            time_slot=self.time_slot,
            status__in=active_statuses,
        ).exclude(pk=self.pk)

        if conflict.exists():
            raise ValidationError({
                    "time_slot": "This table is already booked at that time slot!"
                })

        weekday = self.date.weekday()

        weekday_map = {
            0: DayofWeek.MONDAY,
            1: DayofWeek.TUESDAY,
            2: DayofWeek.WEDNESDAY,
            3: DayofWeek.THURSDAY,
            4: DayofWeek.FRIDAY,
            5: DayofWeek.SATURDAY,
            6: DayofWeek.SUNDAY,
        }
        day_value = weekday_map[weekday]

        working = WorkingHour.objects.filter(day_of_week=day_value).first()

        if not working:
            raise ValidationError({
                    "date": "Cafe is closed in that day!"
                })
        else:
            if self.time_slot.start_time < working.start_time or self.time_slot.start_time > working.end_time:
                raise ValidationError({
                    "time_slot": "Outside working hours!"
                })
        
        if self.time_slot.table and self.number_of_people:
            if self.number_of_people > self.time_slot.table.capacity:
                raise ValidationError({
                    "number_of_people": "Exceeds table capacity!"
                })

        if self.time_slot.table and not self.time_slot.table.is_active:
            raise ValidationError({
                "time_slot": "This table is not active and cannot be reserved."
        })

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.is_finished() and self.status not in [Status.COMPELETED, Status.CANCELED]:
            self.status = Status.COMPELETED
        super().save(*args, **kwargs)

        new_total = self.calculate_total_price()
        if self.total_price != new_total:
            Reservation.objects.filter(pk=self.pk).update(
                total_price=new_total
            )

    def __str__(self):
        return f"Reservation {self.id} - ${self.total_price}"

class ReservationFood(BaseModel):
    quantity = models.PositiveIntegerField(
        verbose_name="Quantity"
    )

    final_price = models.DecimalField(
        editable=False,
        verbose_name="Final Price",
        max_digits=10,
        decimal_places=2,
    )

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        verbose_name="Reservation",
        related_name="reservation_foods",
    )

    food_item = models.ForeignKey(
        FoodItem,
        on_delete=models.CASCADE,
        verbose_name="Food Item",
        related_name="reservation_foods"
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    def clean(self):
        super().clean()

        if self.food_item and not self.food_item.is_available:
            raise ValidationError({
                "food_item": "This food item is not available!"
            })
    
    def save(self, *args, **kwargs):
        existing = ReservationFood.objects.filter(
            reservation=self.reservation,
            food_item=self.food_item
        ).exclude(pk=self.pk).first()

        if existing:
            existing.quantity += self.quantity
            existing.save()
            return

        base = Decimal(self.food_item.price)

        if self.food_item.discount:
            base = self.food_item.discount.apply_to_price(base)

        if self.food_item.category.discount:
            base = self.food_item.category.discount.apply_to_price(base)

        self.final_price = base * self.quantity

        super().save(*args, **kwargs)

    def __str__(self):
        if self.quantity <= 1:
            plural = self.food_item.name

        else:
            if self.food_item.name.endswith("y") and self.food_item.name[-2].lower() not in "aeiou":
                plural = self.food_item.name[:-1] + "ies"
            else:
                plural = self.food_item.name + "s"

        return f"Reservation {self.reservation.id} - {self.quantity} {plural}"

class Comment(BaseModel):
    user = models.OneToOneField(
        User,
        verbose_name="User",
        on_delete=models.CASCADE,
        related_name="comments"
    )

    reservation = models.OneToOneField(
        Reservation,
        verbose_name="Reservation",
        on_delete=models.CASCADE,
    )

    comment = models.TextField(
        max_length=256,
        verbose_name="Comment",
    )

    rating = models.IntegerField(
        verbose_name="Rating",
        choices=Rating.choices,
        default=5,
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    def clean(self):
        super().clean()

        if self.reservation and self.user:
            if self.reservation.user_id != self.user_id:
                raise ValidationError({
                    "user": "User must match the reservation owner."
                })
    def __str__(self):
        return f"{self.comment}"

class Reply(BaseModel):
    class Meta:
        verbose_name_plural = "Replies"

    user = models.ForeignKey(
        User,
        verbose_name="Admin",
        on_delete=models.CASCADE,
        related_name="replies"
    )

    comment = models.OneToOneField(
        Comment,
        verbose_name="Review",
        on_delete=models.CASCADE,
        related_name="replies"
    )

    reply = models.TextField(
        max_length=256,
        verbose_name="Reply",
    ) 

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    def clean(self):

        if self.comment.user_id == self.user_id:
            raise ValidationError({
                "admin": "You cannot reply to your own review."
            })
        
        if not self.user.is_staff:
            raise ValidationError({
                "admin": "Only admins can reply to reviews."
            })
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reply}"