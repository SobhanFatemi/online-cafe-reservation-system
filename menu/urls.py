from django.urls import path
from .views import MenuView, FoodDetailView

urlpatterns = [
    path("", MenuView.as_view(), name="menu_list"),
    path("<int:pk>/", FoodDetailView.as_view(), name="food_detail"),
]