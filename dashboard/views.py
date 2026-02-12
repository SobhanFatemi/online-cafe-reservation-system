from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, UpdateView, View
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from reservations.models import Reservation, TimeSlot
from seating.models import CafeTable, WorkingHour
from menu.models import FoodItem, Category
from .models import CafeSetting

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        return redirect("home")

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()

        context["today_reservations"] = Reservation.objects.filter(date=today).count()
        context["pending"] = Reservation.objects.filter(status="PEN").count()
        context["confirmed"] = Reservation.objects.filter(status="CON").count()
        context["completed"] = Reservation.objects.filter(status="COM").count()
        context["canceled"] = Reservation.objects.filter(status="CAN").count()

        return context

class CafeSettingsView(AdminRequiredMixin, UpdateView):
    model = CafeSetting
    fields = [
        "cancel_window_hours",
        "allow_user_cancel",
        "allow_admin_late_cancel",
        "reservations_enabled",
        "slot_duration_minutes",
        "auto_generate_days_ahead",
    ]
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("admin_settings")

    def get_object(self):
        return CafeSetting.objects.first()

class WorkingHoursView(AdminRequiredMixin, ListView):
    model = WorkingHour
    template_name = "dashboard/working_hours.html"

class TableListView(AdminRequiredMixin, ListView):
    model = CafeTable
    template_name = "dashboard/tables.html"

class TableUpdateView(AdminRequiredMixin, UpdateView):
    model = CafeTable
    fields = ["capacity", "price_per_person", "is_active"]
    template_name = "dashboard/table_edit.html"
    success_url = reverse_lazy("admin_tables")

class GenerateWeeklySlotsView(AdminRequiredMixin, View):
    def post(self, request):
        today = timezone.now().date()
        settings = CafeSetting.load()

        tables = CafeTable.objects.filter(is_active=True)

        for i in range(settings.auto_generate_days_ahead):
            day = today + timedelta(days=i)

            for table in tables:
                start_time = datetime.combine(day, datetime.strptime("09:00", "%H:%M").time())
                end_time = datetime.combine(day, datetime.strptime("23:00", "%H:%M").time())

                current = start_time
                while current < end_time:
                    slot_end = current + timedelta(
                        minutes=settings.slot_duration_minutes
                    )

                    TimeSlot.objects.get_or_create(
                        date=day,
                        table=table,
                        start_time=current.time(),
                        end_time=slot_end.time(),
                    )

                    current = slot_end

        messages.success(request, "Weekly slots generated.")
        return redirect("admin_dashboard")

class ClearSlotsView(AdminRequiredMixin, View):
    def post(self, request):
        today = timezone.now().date()
        TimeSlot.objects.filter(date__gte=today).delete()

        messages.success(request, "Future slots cleared.")
        return redirect("admin_dashboard")

class DiscountListView(AdminRequiredMixin, ListView):
    model = FoodItem
    template_name = "dashboard/discounts.html"

    def get_queryset(self):
        return FoodItem.objects.filter(discount__gt=0)

class ApplyCategoryDiscountView(AdminRequiredMixin, View):
    def post(self, request, pk):
        percentage = request.POST.get("percentage")
        category = Category.objects.get(pk=pk)

        FoodItem.objects.filter(category=category).update(discount=percentage)

        messages.success(request, "Discount applied to category.")
        return redirect("admin_discounts")

class AdminReservationListView(AdminRequiredMixin, ListView):
    model = Reservation
    template_name = "dashboard/reservations.html"
    ordering = ["-date"]

