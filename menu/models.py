from django.db import models
from django.core.exceptions import ValidationError
from common.models import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator
from .choices import Type
from decimal import Decimal, ROUND_HALF_UP

class Discount(BaseModel):
    discount_type = models.CharField(
        verbose_name="Type",
        max_length=3,
        choices=Type.choices,
    )

    amount = models.PositiveIntegerField(
        verbose_name="Amount",
    )

    description = models.TextField(
        verbose_name="Description",
        max_length=256,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    
    def apply_to_price(self, price):

        if self.discount_type == Type.PERCENT:
            return price * (Decimal("1") - Decimal(self.amount) / Decimal("100"))

        if self.discount_type == Type.FIXED:
            return max(price - Decimal(self.amount), Decimal("0"))

        return price

    def clean(self):
        super().clean()

        if self.discount_type == Type.PERCENT:
            if not (0 <= self.amount <= 100):
                raise ValidationError({
                    "amount": "Percent discount must be between 0 and 100."
                })

        if self.discount_type == Type.FIXED:
            if self.amount <= 0:
                raise ValidationError({
                    "amount": "Fixed discount must be greater than 0."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.discount_type == Type.PERCENT:
            return f"{self.amount}%"
        
        elif self.discount_type == Type.FIXED:
            return f"${self.amount}"

class Category(BaseModel):
    class Meta:
        verbose_name_plural = "Categories"
        
    name = models.CharField(
        max_length=32,
        verbose_name="Name"
    )

    discount = models.ForeignKey(
        Discount,
        verbose_name="Discount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="categories"
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
        return f"{self.name}"

class FoodItem(BaseModel):
    name = models.CharField(
        max_length=32,
        verbose_name="Name"
    )

    price = models.DecimalField(
        verbose_name="Price",
        validators=[MinValueValidator(0)],
        max_digits=10,
        decimal_places=2,
    )

    discount = models.ForeignKey(
        Discount,
        verbose_name="Discount",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="foods"
    )

    is_available = models.BooleanField(
        default=True,
        verbose_name="Is Available"
    )

    category = models.ForeignKey(
        Category,
        verbose_name="Category",
        on_delete=models.CASCADE,
        related_name="food_items"
    )

    description = models.TextField(
        verbose_name="Description",
        max_length=256,
        null=True,
        blank=True,
    )

    image = models.ImageField(
        upload_to="food_images/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        verbose_name="Write Time",
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        verbose_name="Update Time",
        auto_now=True,
    )

    def get_discounted_price(self):
        price = self.price

        if self.discount:
            price = self.discount.apply_to_price(price)

        if self.category.discount:
            price = self.category.discount.apply_to_price(price)

        return price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def clean(self):
        super().clean()

        if self.discount and self.discount.discount_type == Type.FIXED:
            if self.discount.amount > self.price:
                raise ValidationError({
                    "discount": "Fixed discount cannot exceed food price."
                })

    def __str__(self):
        return f"{self.name}"