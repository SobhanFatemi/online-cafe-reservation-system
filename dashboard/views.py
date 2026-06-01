from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError
from django.views.generic import (
    TemplateView, ListView, UpdateView,
    CreateView, DeleteView, View, DetailView
)
import logging
from django import forms
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta, time, date as d

from reservations.models import Reservation, TimeSlot, Comment, Reply
from seating.models import CafeTable, WorkingHour
from menu.models import FoodItem, Category, Discount
from .models import CafeSetting
from .forms import ReplyForm
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
        context["cancelled"] = Reservation.objects.filter(status="CAN").count()

        return context

class AdminReservationListView(AdminRequiredMixin, ListView):
    model = Reservation
    template_name = "dashboard/reservations.html"
    context_object_name = "reservations"
    ordering = ["-date"]

class AdminReservationDetailView(AdminRequiredMixin, View):
    template_name = "dashboard/reservation_detail.html"

    def get(self, request, pk):
        reservation = get_object_or_404(
            Reservation.objects
            .select_related("time_slot", "time_slot__table", "user")
            .prefetch_related("reservation_foods__food_item"),
            pk=pk
        )

        context = {
            "object": reservation,
            "can_admin_cancel": reservation.can_admin_cancel(),
        }

        return render(request, self.template_name, context)

    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        status = request.POST.get("status")
        presence = request.POST.get("attendance_status")

        if status == "CAN":
            if not reservation.can_admin_cancel():
                messages.error(request, "Cannot cancel this reservation.")
                return redirect("admin_reservation_detail", pk=pk)

        if status in ["PEN", "CON", "COM", "CAN"]:
            reservation.status = status

        if presence in ["PRE", "ABS", "UNK"]:
            reservation.attendance_status = presence

        reservation.save()

        return redirect("admin_reservation_detail", pk=pk)
    
class AdminReservationCancelView(AdminRequiredMixin, View):
    def post(self, request, pk):
        reservation = get_object_or_404(Reservation, pk=pk)

        if not reservation.can_admin_cancel():
            messages.error(request, "Admin cancel window has expired.")
            return redirect("admin_reservation_detail", pk=pk)

        reservation.status = "CAN"
        reservation.save()

        messages.success(request, "Reservation canceled successfully.")
        return redirect("admin_reservation_detail", pk=pk)

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
    fields = ["name", "category", "price", "description", "discount", "image", "is_available"]
    template_name = "dashboard/food_form.html"
    success_url = reverse_lazy("food")

class FoodUpdateView(AdminRequiredMixin, UpdateView):
    model = FoodItem
    fields = ["name", "category", "price", "description", "discount", "image", "is_available"]
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

        slot_minutes = settings.slot_duration_minutes
        generate_days = settings.auto_generate_days_ahead

        created_count = 0
        skipped_count = 0

        for day_offset in range(generate_days):
            current_date = today + timedelta(days=day_offset)
            weekday_code = DayofWeek.values[current_date.weekday()]

            day_hours = working_hours.filter(day_of_week=weekday_code)
            if not day_hours.exists():
                continue

            for hours in day_hours:
                start_dt = datetime.combine(current_date, hours.start_time)
                end_dt = datetime.combine(current_date, hours.end_time)

                current_dt = start_dt

                while current_dt + timedelta(minutes=slot_minutes) <= end_dt:
                    slot_end = current_dt + timedelta(minutes=slot_minutes)
                    duration = int((slot_end - current_dt).total_seconds() / 60)

                    for table in tables:
                        existing_slot = TimeSlot.objects.filter(
                            date=current_date,
                            table=table,
                            start_time=current_dt.time(),
                            end_time=slot_end.time(),
                        ).first()

                        if existing_slot:
                            skipped_count += 1
                        else:
                            TimeSlot.objects.create(
                                date=current_date,
                                table=table,
                                start_time=current_dt.time(),
                                end_time=slot_end.time(),
                                duration_minutes=duration,
                            )
                            created_count += 1

                    current_dt = slot_end

        if created_count:
            messages.success(request, f"{created_count} slots generated successfully.")
        if skipped_count:
            messages.info(request, f"{skipped_count} slots already existed or were skipped.")

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

class TimeSlotListView(View):
    def get(self, request):
        slots = TimeSlot.objects.order_by("-date", "start_time")
        return render(request, "dashboard/time_slots.html", {
            "time_slots": slots
        })

class TimeSlotCreateView(View):
    def get(self, request):
        tables = CafeTable.objects.filter(is_active=True)
        return render(request, "dashboard/time_slot_form.html", {
            "tables": tables,
            "time_slot": TimeSlot(),
            "is_edit": False,
        })

    def post(self, request):
        table = CafeTable.objects.get(id=request.POST.get("table"))

        slot = TimeSlot(
            table=table,
            date=request.POST.get("date"),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
            note=request.POST.get("note"),
            is_active=request.POST.get("is_active") == "true",
        )

        try:
            slot.full_clean()
            slot.save()
            messages.success(request, "Time slot created successfully.")
            return redirect("dashboard_time_slots")
        except ValidationError as e:
            messages.error(request, e)
            return redirect("dashboard_time_slot_create")

class TimeSlotEditView(AdminRequiredMixin, View):
    template_name = "dashboard/time_slot_edit.html"

    def get(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)
        tables = CafeTable.objects.filter(is_active=True).order_by("table_number")
        return render(request, self.template_name, {"slot": slot, "tables": tables})

    def post(self, request, pk):
        slot = get_object_or_404(TimeSlot, pk=pk)

        table_id = request.POST.get("table")
        date_str = request.POST.get("date")
        start_str = request.POST.get("start_time")
        end_str = request.POST.get("end_time")
        note = request.POST.get("note")
        is_active = request.POST.get("is_active") == "true"

        

        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_obj = datetime.strptime(start_str, "%H:%M").time()
        end_obj = datetime.strptime(end_str, "%H:%M").time()

        if start_obj >= end_obj:
            messages.error(request, "End time must be after start time.")
            return redirect("dashboard_time_slot_edit", pk=pk)

        s = datetime.combine(d.today(), start_obj)
        e = datetime.combine(d.today(), end_obj)
        duration = int((e - s).seconds / 60)

        slot.table = CafeTable.objects.get(id=table_id)
        slot.date = date_obj
        slot.start_time = start_obj
        slot.end_time = end_obj
        slot.duration_minutes = duration
        slot.note = note or ""
        slot.is_active = is_active

        try:
            slot.full_clean()
            slot.save()
            messages.success(request, "Time slot updated successfully.")
        except ValidationError as e:
            messages.error(request, e.messages[0])

        return redirect("dashboard_time_slots")

class TimeSlotDeleteView(AdminRequiredMixin, DeleteView):
    model = TimeSlot
    template_name = "dashboard/time_slot_confirm_delete.html"
    success_url = reverse_lazy("dashboard_time_slots")

class CommentsListView(AdminRequiredMixin, View):
    def get(self, request):
        comments = (
            Comment.objects
            .select_related("user", "reservation")
            .prefetch_related("replies") 
            .order_by("-created_at")
        )

        return render(request, "dashboard/comments.html", {
            "comments": comments
        })

class ReplyToCommentView(AdminRequiredMixin, View):
    template_name = "dashboard/comment_reply_form.html"

    def get(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        reply = Reply.objects.filter(comment=comment).first()
        form = ReplyForm(instance=reply)

        return render(
            request,
            self.template_name,
            {"form": form, "comment": comment, "reply": reply}
        )

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        reply = Reply.objects.filter(comment=comment).first()
        form = ReplyForm(request.POST, instance=reply)

        if form.is_valid():
            reply = form.save(commit=False)
            reply.comment = comment
            reply.user = request.user
            reply.save()

            messages.success(request, "Reply saved successfully.")
            return redirect("dashboard-comments")

        return render(
            request,
            self.template_name,
            {"comment": comment, "form": form, "reply": reply}
        )
    
class ReplyDeleteView(AdminRequiredMixin, View):
    def post(self, request, reply_id):
        reply = get_object_or_404(Reply, id=reply_id)
        reply.delete()

        messages.success(request, "Reply deleted successfully.")
        return redirect("dashboard-comments")