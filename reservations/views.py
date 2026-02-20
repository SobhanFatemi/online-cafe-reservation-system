from django.shortcuts import render, get_object_or_404, redirect
from .models import Reservation
from menu.models import FoodItem
from reservations.models import ReservationFood  # your through model

def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)

    # Food items related to this reservation
    foods = reservation.reservation_foods.all()

    # Price breakdown
    table_price = reservation.time_slot.table.price_per_person * reservation.number_of_people
    food_total = sum(item.final_price for item in foods)
    total_price = table_price + food_total

    context = {
        "reservation": reservation,
        "foods": foods,
        "table_price": table_price,
        "food_total": food_total,
        "total_price": total_price,
    }

    return render(request, "reservations/reservation_detail.html", context)

def add_food_to_reservation(request, reservation_id, food_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    food = get_object_or_404(FoodItem, pk=food_id)

    ReservationFood.objects.create(
        reservation=reservation,
        food_item=food,
        final_price=food.price
    )

    reservation.update_total_price()

    return redirect("reservation_detail", pk=reservation_id)
