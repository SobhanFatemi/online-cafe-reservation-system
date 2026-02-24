from django.views.generic import CreateView, View
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from django.contrib.auth.forms import AuthenticationForm


from .forms import SignupForm

User = get_user_model()


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_link = self.request.build_absolute_uri(
            reverse("users:activate", kwargs={"uidb64": uid, "token": token})
        )

        send_mail(
            "Activate your account",
            f"Click the link to activate your account:\n{activation_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )

        messages.success(
            self.request,
            "Account created. Please check your email to activate your account."
        )

        return super().form_valid(form)

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except:
            user = None

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, "Account activated. You can now login.")
            return redirect("login")
        else:
            return render(request, "registration/activation_invalid.html")

class SilentAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "",
        "inactive": "",
    }

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = SilentAuthenticationForm

    def form_invalid(self, form):
        username = self.request.POST.get("username")
        password = self.request.POST.get("password")

        try:
            user = User.objects.get(username=username)

            if user.check_password(password) and not user.is_active:

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = account_activation_token.make_token(user)

                activation_link = self.request.build_absolute_uri(
                    reverse("users:activate", kwargs={"uidb64": uid, "token": token})
                )

                send_mail(
                    "Activate your account",
                    f"Click the link to activate your account:\n{activation_link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )

                messages.success(
                    self.request,
                    "Your account is not activated. A new activation email has been sent."
                )

                return redirect("login")

        except User.DoesNotExist:
            pass

        messages.error(
            self.request,
            "Invalid username or password."
        )

        return redirect("login")