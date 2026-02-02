from django.shortcuts import render
from django.views.generic import ListView
from .models import Category

class MenuView(ListView):
    model = Category
    template_name = "menu/menu.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.prefetch_related("food_items")
