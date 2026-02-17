from django.urls import path
from .views import MenuView ,food_detail

urlpatterns = [
    path("menu/", MenuView.as_view(template_name="menu/menu.html"), name="menu"),
    path('food/<int:pk>/', food_detail, name='food-detail'),
]
