from django import forms
from .models import Reservation, Comment

class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ["date", "time_slot", "number_of_people", "note"]

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["comment", "rating"]
        widgets = {
            "comment": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write your comment..."
            }),
            "rating": forms.Select(attrs={"class": "form-control"}),
        }