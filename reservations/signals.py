from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ReservationFood

@receiver(post_save, sender=ReservationFood)
def update_total_after_food_save(sender, instance, **kwargs):
    instance.reservation.update_total_price()

@receiver(post_delete, sender=ReservationFood)
def update_total_after_food_delete(sender, instance, **kwargs):
    instance.reservation.update_total_price()