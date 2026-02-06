from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.urls import reverse
from .tokens import account_activation_token


User = get_user_model()

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email"]

        widgets = {
            "username": forms.TextInput(attrs={"class": ""}),
            "email": forms.EmailInput(attrs={"class": ""}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False

        if commit:
            user.save()

        return user


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Username or password is incorrect.",
        "inactive": "Your account is not activated yet."
    }
    
    def confirm_login_allowed(self, user):
        if not user.is_active:

            request = self.request

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = account_activation_token.make_token(user)

            link = request.build_absolute_uri(
                reverse("activate", args=[uid, token])
            )

            send_mail(
                "Verify your account",
                f"Click to activate:\n{link}",
                settings.EMAIL_HOST_USER,
                [user.email],
            )

            raise forms.ValidationError(
                "Account not activated. Activation email sent!",
                code="inactive",
            )
