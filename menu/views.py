from django.shortcuts import render
from django.db.models import Avg, Prefetch
from django.views.generic import ListView, DetailView
from reservations.models import Comment
from .models import Category, FoodItem

class MenuView(ListView):
    model = Category
    template_name = "menu/menu.html"
    context_object_name = "categories"

    def get_queryset(self):
        food_qs = FoodItem.objects.annotate(
            avg_rating=Avg("reservation_foods__reservation__comments__rating")
        )
        return Category.objects.prefetch_related(
            Prefetch("food_items", queryset=food_qs)
        )

class FoodDetailView(DetailView):
    model = FoodItem
    template_name = "menu/food_detail.html"
    context_object_name = "food"

    def get_queryset(self):
        return FoodItem.objects.annotate(
            avg_rating=Avg("reservation_foods__reservation__comments__rating")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        food = self.object

        reservation_ids = (
            food.reservation_foods
            .values_list("reservation_id", flat=True)
        )

        comments = (
            Comment.objects
            .filter(reservation_id__in=reservation_ids)
            .select_related("reservation", "user")
            .prefetch_related("replies")
            .order_by("-created_at")
        )

        context["comments"] = comments
        return context