from django.urls import path
from .views import (
    ReservationCreateView,
    MyReservationsView,
    ReservationDetailView,
    ReservationCancelView,
    ReservationOrderView,
    ReservationCommentCreateView,
    CommentUpdateView,
    CommentDeleteView
)

urlpatterns = [
    path("create/", ReservationCreateView.as_view(), name="make_reservation"),
    path("my/", MyReservationsView.as_view(), name="my_reservations"),
    path("<int:pk>/", ReservationDetailView.as_view(), name="reservation_detail"),
    path("<int:pk>/cancel/", ReservationCancelView.as_view(), name="cancel_reservation"),
    path("<int:pk>/order/", ReservationOrderView.as_view(), name="reservation_order"),
    path("reservation/<int:pk>/comment/", ReservationCommentCreateView.as_view(), name="reservation_comment"),
    path("comments/<int:pk>/edit/", CommentUpdateView.as_view(),name="comment-edit"),
    path("comments/<int:pk>/delete/", CommentDeleteView.as_view(),name="comment-delete"),
]