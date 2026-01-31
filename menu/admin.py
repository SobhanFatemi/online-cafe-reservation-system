from django.contrib import admin
from common.admin import BaseAdmin
from .models import Category, FoodItem, Discount


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ("id", "name", "discount")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(FoodItem)
class FoodItemAdmin(BaseAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "price",
        "discount",
        "is_available",
    )
    search_fields = ("name", "category__name")
    list_filter = ("is_available", "category")
    list_select_related = ("category",)
    ordering = ("name",)

@admin.register(Discount)
class Discount(BaseAdmin):
    list_display = (
        "id",
        "discount_type",
        "amount", 
        "description",
        "created_at"
    )
    list_filter = ("discount_type", "created_at")
    search_fields = ("description",)
    ordering = ("-created_at",)

