from django.db import models
from common.models import BaseModel
from django.core.validators import MaxValueValidator, MinValueValidator

#Models
class Category(BaseModel):

    class Meta:
        verbose_name_plural = "Categories"
        
    name = models.CharField(
        max_length=32,
        verbose_name="Name"
    )

    discount_percent = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Discount (Percent)"
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

    price = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Price",
    )

    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Discount (Percent)"
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