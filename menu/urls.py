from django.urls import path
from .views import MenuView
from. import views

urlpatterns = [
    path("menu/", MenuView.as_view(template_name="menu/menu.html"), name="menu"),
    path('food/<int:pk>/', views.food_detail, name='food_detail'), 
    path('add/', views.add_to_reservation, name='add_to_reservation'),
]
