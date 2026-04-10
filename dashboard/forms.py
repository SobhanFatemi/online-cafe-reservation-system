from django import forms
from reservations.models import Reply

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ["reply"]
        widgets = {
            "reply": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Write your reply..."
            })
        }
