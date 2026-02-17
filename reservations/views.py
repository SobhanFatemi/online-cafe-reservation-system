# reservation/views.py

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Reservation, ReservationFood
from .choices import Status
from menu.models import FoodItem


#for (-) less food item 
def get_active_reservation(user):
    return Reservation.objects.filter(
        user=user,
        status=Status.PENDING
    ).first()
@login_required
def increase_food_quantitiy(request , food_id):
    reservation = get_active_reservation(request.user)
    if not reservation: 
        return JsonResponse(
            {'error'},
            Status = 400
        )
    food = get_object_or_404(FoodItem , id = food_id , is_available=True)

    reservation_food, created = ReservationFood.objects.get_or_create(
        reservation=reservation,
        food_item=food,
        defaults={'quantity': 1}
    )

    if not created:
        reservation_food.quantity += 1
        reservation_food.save()

    reservation.update_total_price()
    return JsonResponse(
        {
        'food_id' : food.id,
        'quantity': reservation_food.quantity,
        'total_price': str(reservation.total_price)
        }
    )

def get_active_reservation(user):
    
    return Reservation.objects.filter(
        user=user,
        status=Status.PENDING
    ).first()

#incrasses food count(+)


@login_required
def decrease_food_quantity(request, food_id):
    reservation = get_active_reservation(request.user)

    if not reservation:
        return JsonResponse(
            {'error': 'No active reservation'},
            status=400
        )

    item = ReservationFood.objects.filter(
        reservation=reservation,
        food_item_id=food_id
    ).first()

    if not item:
        return JsonResponse({
            'food_id': food_id,
            'quantity': 0,
            'total_price': str(reservation.total_price)
        })

    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()


    reservation.update_total_price()


    return JsonResponse({
        'food_id': food_id,
        'quantity': item.quantity if item.pk else 0,
        'total_price': str(reservation.total_price)
    })
    