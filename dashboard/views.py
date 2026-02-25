from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.views.generic import (
    TemplateView, ListView, UpdateView,
    CreateView, DeleteView, View
)
from django import forms
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, time

from reservations.models import Reservation, TimeSlot
from seating.models import CafeTable, WorkingHour
from menu.models import FoodItem, Category, Discount
from .models import CafeSetting
from seating.choices import DayofWeek

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

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

class AdminReservationListView(AdminRequiredMixin, ListView):
    model = Reservation
    template_name = "dashboard/reservations.html"
    context_object_name = "reservations"
    ordering = ["-date"]

class AdminReservationDetailView(AdminRequiredMixin, View):
    template_name = "dashboard/reservation_detail.html"

    def get(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)
        return render(request, self.template_name, {"object": reservation})

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        status = request.POST.get("status")
        presence = request.POST.get("attendance_status")

        if status in ["PEN", "CON", "COM", "CAN"]:
            reservation.status = status

        if presence in ["PRE", "ABS", "UNK"]:
            reservation.attendance_status = presence

        reservation.save()

        return redirect("reservation_detail", pk=reservation.pk)

class TableListView(AdminRequiredMixin, ListView):
    model = CafeTable
    template_name = "dashboard/tables.html"
    context_object_name = "tables"
    ordering = ["-id"]

class TableCreateView(AdminRequiredMixin, CreateView):
    model = CafeTable
    fields = ["table_number", "capacity", "price_per_person", "is_active"]
    template_name = "dashboard/table_form.html"
    success_url = reverse_lazy("tables")

class TableDeleteView(DeleteView):
    model = CafeTable
    template_name = "dashboard/table_confirm_delete.html"
    success_url = reverse_lazy("tables")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        future_reservations = Reservation.objects.filter(
            time_slot__table=self.object,
            date__gte=timezone.now().date()
        ).exists()

        if future_reservations:
            messages.error(
                request,
                "Cannot delete table with future reservations."
            )
            return redirect("tables")

        messages.success(request, "Table deleted successfully.")
        return super().post(request, *args, **kwargs)
    
class TableUpdateView(AdminRequiredMixin, UpdateView):
    model = CafeTable
    fields = ["capacity", "price_per_person", "is_active"]
    template_name = "dashboard/table_form.html"
    success_url = reverse_lazy("tables")

class FoodListView(AdminRequiredMixin, ListView):
    model = FoodItem
    template_name = "dashboard/food_list.html"
    context_object_name = "foods"
    ordering = ["-id"]

class FoodCreateView(AdminRequiredMixin, CreateView):
    model = FoodItem
    fields = ["name", "category", "price", "description", "image", "is_available"]
    template_name = "dashboard/food_form.html"
    success_url = reverse_lazy("food")

class FoodUpdateView(AdminRequiredMixin, UpdateView):
    model = FoodItem
    fields = ["name", "category", "price", "description", "image", "is_available"]
    template_name = "dashboard/food_form.html"
    success_url = reverse_lazy("food")

class FoodDeleteView(AdminRequiredMixin, DeleteView):
    model = FoodItem
    template_name = "dashboard/food_confirm_delete.html"
    success_url = reverse_lazy("food")

class CategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = "dashboard/categories.html"
    context_object_name = "categories"
    ordering = ["-id"]

class CategoryCreateView(AdminRequiredMixin, CreateView):
    model = Category
    fields = ["name"]
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("categories")

class CategoryDeleteView(DeleteView):
    model = Category
    template_name = "dashboard/category_confirm_delete.html"
    success_url = reverse_lazy("categories")

class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    fields = ["name"]
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("categories")

class CafeSettingsView(AdminRequiredMixin, UpdateView):
    model = CafeSetting
    fields = "__all__"
    template_name = "dashboard/settings.html"
    success_url = reverse_lazy("dashboard")

    def get_object(self):
        return CafeSetting.objects.first()
    
class GenerateSlotsView(AdminRequiredMixin, View):

    def post(self, request):
        settings = CafeSetting.load()

        if not settings:
            messages.error(request, "Cafe settings not configured.")
            return redirect("dashboard")

        today = timezone.now().date()

        tables = CafeTable.objects.filter(is_active=True)
        working_hours = WorkingHour.objects.filter(is_closed=False)

        if not working_hours.exists():
            messages.error(request, "Working hours are not defined.")
            return redirect("dashboard")

        created_count = 0
        skipped_count = 0

        for day_offset in range(settings.auto_generate_days_ahead):
            current_date = today + timedelta(days=day_offset)

            weekday_code = DayofWeek.values[current_date.weekday()]
            day_hours = working_hours.filter(day_of_week=weekday_code)

            for hours in day_hours:

                start_dt = datetime.combine(current_date, hours.start_time)
                end_dt = datetime.combine(current_date, hours.end_time)

                current_time = start_dt

                while current_time < end_dt:
                    slot_end = current_time + timedelta(
                        minutes=settings.slot_duration_minutes
                    )

                    if slot_end > end_dt:
                        break

                    for table in tables:
                        try:
                            slot, created = TimeSlot.objects.get_or_create(
                                date=current_date,
                                table=table,
                                start_time=current_time.time(),
                                end_time=slot_end.time(),
                            )

                            if created:
                                created_count += 1
                            else:
                                skipped_count += 1

                        except (ValidationError, IntegrityError):
                            skipped_count += 1
                            continue

                    current_time = slot_end

        if created_count > 0:
            messages.success(
                request,
                f"{created_count} slots generated successfully."
            )

        if skipped_count > 0:
            messages.info(
                request,
                f"{skipped_count} slots already existed and were skipped."
            )

        return redirect("dashboard")
    
class ClearSlotsView(AdminRequiredMixin, View):

    def post(self, request):
        today = timezone.now().date()

        future_slots = TimeSlot.objects.filter(date__gte=today)

        free_slots = future_slots.filter(reservations__isnull=True)

        deleted_count = free_slots.count()

        free_slots.delete()

        messages.success(
            request,
            f"{deleted_count} future unused slots cleared successfully."
        )

        return redirect("dashboard")
    
class WorkingHourForm(forms.ModelForm):
    class Meta:
        model = WorkingHour
        fields = ["start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

class WorkingHoursListView(AdminRequiredMixin, ListView):
    model = WorkingHour
    template_name = "dashboard/working_hours.html"
    context_object_name = "working_hours"

    def get_queryset(self):
        for day in DayofWeek.values:
            WorkingHour.objects.get_or_create(
                day_of_week=day,
                defaults={
                    "start_time": time(9, 0),
                    "end_time": time(22, 0),
                    "is_closed": False
                }
            )

        return WorkingHour.objects.all().order_by("day_of_week")

class WorkingHourUpdateView(AdminRequiredMixin, UpdateView):
    model = WorkingHour
    form_class = WorkingHourForm
    template_name = "dashboard/working_hour_edit.html"
    success_url = reverse_lazy("working_hours")

    def form_valid(self, form):
        messages.success(self.request, "Working hours updated successfully.")
        return super().form_valid(form)
    
class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ["discount_type", "amount", "description"]

class DiscountListView(AdminRequiredMixin, ListView):
    model = Discount
    template_name = "dashboard/discounts.html"
    context_object_name = "discounts"

class DiscountCreateView(AdminRequiredMixin, CreateView):
    model = Discount
    form_class = DiscountForm
    template_name = "dashboard/discount_form.html"
    success_url = reverse_lazy("discounts")

    def form_valid(self, form):
        messages.success(self.request, "Discount created successfully.")
        return super().form_valid(form)

class DiscountUpdateView(AdminRequiredMixin, UpdateView):
    model = Discount
    form_class = DiscountForm
    template_name = "dashboard/discount_form.html"
    success_url = reverse_lazy("discounts")

    def form_valid(self, form):
        messages.success(self.request, "Discount updated successfully.")
        return super().form_valid(form)

class DiscountDeleteView(AdminRequiredMixin, DeleteView):
    model = Discount
    template_name = "dashboard/discount_confirm_delete.html"
    success_url = reverse_lazy("discounts")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Discount deleted.")
        return super().delete(request, *args, **kwargs)