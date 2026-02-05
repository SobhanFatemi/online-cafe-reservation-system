from django.contrib import admin
from common.admin import BaseAdmin
from .models import Category, FoodItem


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    list_display = ("id", "name", "discount_percent")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(FoodItem)
class FoodItemAdmin(BaseAdmin):
    list_display = (
        "id",
        "name",
        "category",
        "price",
        "discount_percent",
        "is_available",
    )
    search_fields = ("name", "category__name")
    list_filter = ("is_available", "category")
    list_select_related = ("category",)
    ordering = ("name",)

