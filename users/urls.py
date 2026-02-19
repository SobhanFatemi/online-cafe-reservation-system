from django.urls import path
from django.contrib.auth.views import LogoutView
from django.views.generic import TemplateView
from .views import SignupView, ActivateAccountView, ResendActivationView, CustomLoginView

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("activate/<uidb64>/<token>", ActivateAccountView.as_view(), name="activate"),
    path("resend-activation/", ResendActivationView.as_view(), name="resend_activation"),
    path("activation-sent/", TemplateView.as_view(
        template_name="users/activation_sent.html"
    ), name="activation_sent"),

]
