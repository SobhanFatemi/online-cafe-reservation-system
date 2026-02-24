from django.shortcuts import render
from django.db.models import Avg, Prefetch
from django.views.generic import ListView, DetailView
from .models import Category, FoodItem

class MenuView(ListView):
    model = Category
    template_name = "menu/menu.html"
    context_object_name = "categories"

    def get_queryset(self):
        food_qs = FoodItem.objects.annotate(
            avg_rating=Avg("reservation_foods__reservation__comment__rating")
        )
        return Category.objects.prefetch_related(
            Prefetch("food_items", queryset=food_qs)
        )

class FoodDetailView(DetailView):
    pass