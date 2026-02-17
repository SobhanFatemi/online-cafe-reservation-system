from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from .models import Category, FoodItem


def food_detail(request, pk):
    food = get_object_or_404(
        FoodItem.objects.annotate(
            avg_rating=Avg("reservation_foods__reservation__comment__rating"),
            rating_count=Count("reservation_foods__reservation__comment"),
        ),
        pk=pk,
        is_available=True,
    )

    comments = (
        food.reservation_foods
        .filter(reservation__comment__isnull=False)
        .select_related("reservation")
        .prefetch_related("reservation__comment")
    )

    related_foods = (
        FoodItem.objects.filter(
            category=food.category,
            is_available=True,
        )
        .exclude(id=food.id)
        .annotate(
            avg_rating=Avg("reservation_foods__reservation__comment__rating")
        )[:4]
    )

    return render(request, "menu/food_detail.html", {
        "food": food,
        "comments": comments,
        "related_foods": related_foods,
    })
