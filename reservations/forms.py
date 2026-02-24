from django import forms
from .models import Reservation

class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["date", "time_slot", "number_of_people", "note"]

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }