from django.db import models
from seating.models import CafeTable, TimeSlot
from menu.models import FoodItem
from django.core.validators import MinValueValidator
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Status(models.TextChoices):
    PENDING = "PEN", "Pending"
    CONFIRMED = "CON", "Confirmed"
    CANCELLED = "CAN", "Cancelled"
    COMPELETED = "COM", "Compeleted"

class AttendanceStatus(models.TextChoices):
    UNKNOWN = "UNK", "Unknown"
    PRESENT = "PRE", "Present"
    ABSENT = "ABS", "Absent"

class Reservation(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="User",
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    table = models.ForeignKey(
        CafeTable,
        verbose_name="Table",
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    date = models.DateField(
        verbose_name="Reservation Date"
    )

    time_slot = models.ForeignKey(
        TimeSlot,
        verbose_name="Time Slot",
        on_delete=models.CASCADE,
        related_name="reservations"

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
            )["total"] or 0
        )

        table_total = self.table.price_per_person * self.number_of_people

        return food_total + table_total

    def update_total_price(self):
        self.total_price = self.calculate_total_price()
        self.save(update_fields=["total_price"])


    def clean(self):
        if self.table and self.number_of_people:
            if self.number_of_people > self.table.capacity:
                raise ValidationError({
                    "number_of_people": "Exceeds table capacity!"
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        new_total = self.calculate_total_price()
        if self.total_price != new_total:
            Reservation.objects.filter(pk=self.pk).update(
                total_price=new_total
            )

    def __str__(self):
        return f"{self.user.username}: Table #{self.table.table_number} - ${self.total_price}"

class ReservationFood(models.Model):
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
        if self.food_item and not self.food_item.is_available:
            raise ValidationError({
                "food_item": "This food item is not available!"
            })
    
    def save(self, *args, **kwargs):
        base = Decimal(self.food_item.price)

        item_discount = str(self.food_item.discount_percent or 0)
        cat_discount = str(self.food_item.category.discount_percent or 0)

        item_factor = Decimal("1") - (Decimal(item_discount) / Decimal("100"))
        cat_factor = Decimal("1") - (Decimal(cat_discount) / Decimal("100"))

        unit_price = base * item_factor * cat_factor

        self.final_price = unit_price * int(self.quantity)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Table #{self.reservation.table.table_number} - {self.quantity} {self.food_item.name}s"