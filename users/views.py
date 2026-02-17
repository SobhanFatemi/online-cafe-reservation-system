from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.auth import login
from .forms import SignupForm


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("menu")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
