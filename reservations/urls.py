from django.urls import path
from .views import (
    ReservationCreateView,
    MyReservationsView,
    ReservationDetailView,
    CancelReservationView,
    ReservationOrderView
)

urlpatterns = [
    path("create/", ReservationCreateView.as_view(), name="make_reservation"),
    path("my/", MyReservationsView.as_view(), name="my_reservations"),
    path("<int:pk>/", ReservationDetailView.as_view(), name="reservation_detail"),
    path("<int:pk>/cancel/", CancelReservationView.as_view(), name="cancel_reservation"),
    path("<int:pk>/order/", ReservationOrderView.as_view(), name="reservation_order"),
]