from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.reservation_lists, name='reservation_lists'),
    path('pending/', views.pending_list, name='pending_list'),
    path('confirmed/', views.confirmed_list, name='confirmed_list'),
    path('cancelled/', views.cancelled_list, name='cancelled_list'),
    path('completed/', views.completed_list, name='completed_list'),
    path('<int:pk>/', views.reservation_detail, name='reservation_detail'),
]