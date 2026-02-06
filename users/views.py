from django.views.generic import CreateView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.conf import settings
from django.shortcuts import redirect
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from .forms import SignupForm, CustomAuthenticationForm
from .tokens import account_activation_token

class SignupView(CreateView):
    form_class = SignupForm
    template_name = "users/signup.html"

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        link = self.request.build_absolute_uri(
            reverse("activate", args=[uid, token])
        )

        send_mail(
            "Verify your account",
            f"Click this link to activate your account:\n{link}",
            settings.EMAIL_HOST_USER,
            [user.email],
        )

        return redirect("activation_sent")

class ActivateAccountView(View):
    def get(self, request, uidb64, token):
        User = get_user_model()

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            user = None

        if user and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()

            return render(
                request,
                "users/activation_success.html",
                {"username": user.username}
            )


        return render(request, "users/activation_invalid.html")

class ResendActivationView(View):
    COOLDOWN_SECONDS = 120

    def post(self, request):
        username = request.POST.get("username")

        if not username:
            messages.error(request, "Username required.")
            return redirect("login")

        User = get_user_model()

        try:
            user = User.objects.get(username=username, is_active=False)
        except User.DoesNotExist:
            messages.error(request, "No inactive user found.")
            return redirect("login")

        last_sent = request.session.get("activation_last_sent")

        if last_sent:
            last_sent = timezone.datetime.fromisoformat(last_sent)
            elapsed = (timezone.now() - last_sent).total_seconds()

            if elapsed < self.COOLDOWN_SECONDS:
                remaining = int(self.COOLDOWN_SECONDS - elapsed)
                request.session["activation_remaining"] = remaining
                return redirect("login")

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

        request.session["activation_last_sent"] = timezone.now().isoformat()
        request.session["activation_remaining"] = self.COOLDOWN_SECONDS

        messages.success(request, "Activation email resent.")
        return redirect("login")

class CustomLoginView(LoginView):
    template_name = "users/login.html"
    authentication_form = CustomAuthenticationForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        last = self.request.session.get("activation_last_sent")

        if last:
            last = timezone.datetime.fromisoformat(last)
            remaining = 120 - int((timezone.now() - last).total_seconds())
            ctx["activation_remaining"] = max(0, remaining)
        else:
            ctx["activation_remaining"] = 0

        return ctx
