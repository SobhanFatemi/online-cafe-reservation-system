from django.contrib import admin, messages
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
    autocomplete_fields = ("discount",)
    search_fields = ("name", "category__name")
    list_filter = ("is_available", "category")
    list_select_related = ("category",)
    ordering = ("name",)

    actions = (
        "available",
        "unavailable",
    )

    @admin.action(description="Available of selected food items")
    def available(self, request, queryset):
        queryset.update(is_available=True)
        self.message_user(request, "Selected food item or food items are available now!", messages.SUCCESS)

    @admin.action(description="Unavailable of selected food items")
    def unavailable(self, request, queryset):
        queryset.update(is_available=False)
        self.message_user(request, "Selected food item or food items are unavailable now!", messages.SUCCESS)

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
    search_fields = ("description", "amount")
    ordering = ("-created_at",)

