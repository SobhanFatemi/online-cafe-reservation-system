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

User = get_user_model()

class Reservation(BaseModel):
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
            )["total"] or Decimal("0")
        )

        table_total = self.table.price_per_person * self.number_of_people

        return food_total + table_total

    def update_total_price(self):
        self.total_price = self.calculate_total_price()
        self.save(update_fields=["total_price"])


    def clean(self):
        super().clean()

        if self.table and self.number_of_people:
            if self.number_of_people > self.table.capacity:
                raise ValidationError({
                    "number_of_people": "Exceeds table capacity!"
                })

        if self.table and not self.table.is_active:
            raise ValidationError({
                "table": "This table is not active and cannot be reserved."
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