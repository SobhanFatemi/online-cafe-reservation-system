from datetime import datetime
from django.utils import timezone
from django.views.generic import CreateView, ListView, DetailView, View
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.db.models import Prefetch
import json

from menu.models import FoodItem, Category
from .models import Reservation, TimeSlot, CafeTable, Status, AttendanceStatus, ReservationFood
from .forms import ReservationCreateForm


class ReservationCreateView(LoginRequiredMixin, CreateView):
    model = Reservation
    form_class = ReservationCreateForm
    template_name = "reservations/make_reservation.html"
    success_url = reverse_lazy("my_reservations")

    def get_available_tables(self, selected_date):
        tables = CafeTable.objects.filter(is_active=True)
        table_data = []

        for table in tables:
            slots = TimeSlot.objects.filter(
                date=selected_date,
                table=table,
                is_active=True
            )

            slot_list = []

            for slot in slots:
                is_reserved = Reservation.objects.filter(
                    date=selected_date,
                    time_slot=slot,
                    status__in=[Status.PENDING, Status.CONFIRMED]
                ).exists()

                slot_list.append({
                    "slot": slot,
                    "is_reserved": is_reserved
                })

            table_data.append({
                "table": table,
                "slots": slot_list,
                "is_available": any(not s["is_reserved"] for s in slot_list)
            })

        return table_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_date = self.request.GET.get("date")
        slot_id = self.request.GET.get("slot")

        context["table_data"] = []
        context["selected_slot"] = None
        context["price_per_person"] = None

        if selected_date:
            try:
                selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
                context["table_data"] = self.get_available_tables(selected_date_obj)
            except:
                pass

        if slot_id:
            try:
                slot = TimeSlot.objects.get(id=slot_id)
                context["selected_slot"] = slot
                context["price_per_person"] = slot.table.price_per_person
            except TimeSlot.DoesNotExist:
                pass

        return context

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.user = self.request.user
        reservation.status = Status.PENDING
        reservation.attendance_status = AttendanceStatus.UNKNOWN

        selected_date = reservation.date
        slot = reservation.time_slot

        reservation_datetime = datetime.combine(
            selected_date,
            slot.start_time
        )
        reservation_datetime = timezone.make_aware(reservation_datetime)

        if reservation_datetime <= timezone.localtime():
            form.add_error(None, "Cannot reserve in the past.")
            return self.form_invalid(form)

        if Reservation.objects.filter(
            date=selected_date,
            time_slot=slot,
            status__in=[Status.PENDING, Status.CONFIRMED]
        ).exists():
            form.add_error(None, "This time slot is already reserved.")
            return self.form_invalid(form)

        reservation.total_price = (
            reservation.number_of_people *
            slot.table.price_per_person
        )

        reservation.save()
        return redirect(self.success_url)

class MyReservationsView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/my_reservations.html"
    context_object_name = "reservations"

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).select_related(
            "time_slot",
            "time_slot__table"
).order_by("-created_at")

class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservations/reservation_detail.html"
    context_object_name = "reservation"

    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).select_related(
            "time_slot",
            "time_slot__table"
        ).prefetch_related("reservation_foods__food_item")

class ReservationOrderView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservations/reservation_order.html"
    context_object_name = "reservation"

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        reservation = self.get_object()

        if reservation.status != Status.PENDING:
            return redirect("reservation_detail", pk=reservation.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reservation = self.object

        existing_items = reservation.reservation_foods.select_related("food_item")

        context["existing_items"] = {
            str(item.food_item.id): {
                "quantity": item.quantity,
                "price": float(item.food_item.get_discounted_price()),
                "name": item.food_item.name
            }
            for item in existing_items
        }

        food_qs = FoodItem.objects.all()
        context["categories"] = Category.objects.prefetch_related(
            Prefetch("food_items", queryset=food_qs)
        )

        return context

    def post(self, request, *args, **kwargs):
        reservation = self.get_object()

        if reservation.status != Status.PENDING:
            return JsonResponse(
                {"error": "You cannot modify this reservation."},
                status=403
            )

        data = json.loads(request.body)
        items = data.get("items", [])

        reservation.reservation_foods.all().delete()

        for item in items:
            food = get_object_or_404(
                FoodItem,
                id=int(item["food_item_id"])
            )
            quantity = int(item["quantity"])

            if quantity > 0:
                ReservationFood.objects.create(
                    reservation=reservation,
                    food_item=food,
                    quantity=quantity
                )

        return JsonResponse({"status": "success"})
    
class CancelReservationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        reservation = get_object_or_404(
            Reservation,
            pk=pk,
            user=request.user
        )

        reservation_datetime = datetime.combine(
            reservation.date,
            reservation.time_slot.start_time
        )
        reservation_datetime = timezone.make_aware(reservation_datetime)

        if reservation_datetime <= timezone.localtime():
            messages.error(request, "Reservation already started.")
            return redirect("reservation_detail", pk=pk)

        reservation.status = Status.CANCELED
        reservation.save()

        messages.success(request, "Reservation cancelled.")
        return redirect("my_reservations")

class MarkAttendanceView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return HttpResponseForbidden()

        reservation = get_object_or_404(Reservation, pk=pk)

        attendance_value = request.POST.get("attendance")

        if attendance_value in [
            AttendanceStatus.PRESENT,
            AttendanceStatus.ABSENT
        ]:
            reservation.attendance_status = attendance_value
            reservation.status = Status.COMPELETED
            reservation.save()

        return redirect("reservation_detail", pk=pk)