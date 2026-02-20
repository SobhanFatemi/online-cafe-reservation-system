from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('reservation/', views.reservation_lists, name='reservation_lists'),
    path('reservation/pending/', views.pending_list, name='pending_list'),
    path('reservation/confirmed/', views.confirmed_list, name='confirmed_list'),
    path('reservation/cancelled/', views.cancelled_list, name='cancelled_list'),
    path('reservation/completed/', views.completed_list, name='completed_list'),
    path('reservation/<int:pk>/', views.reservation_detail, name='reservation_detail'),
]