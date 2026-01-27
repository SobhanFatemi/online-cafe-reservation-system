from django.contrib import admin
from .models import Reservation, ReservationFood, Review, ReviewReply

admin.site.register(Reservation)
admin.site.register(ReservationFood)
admin.site.register(Review)
admin.site.register(ReviewReply)
