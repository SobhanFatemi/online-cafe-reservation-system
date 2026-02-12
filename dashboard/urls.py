from django.urls import path
from .views import (AdminDashboardView, GenerateWeeklySlotsView, 
                    ClearSlotsView, TableListView,
                    TableUpdateView, CafeSettingsView, DiscountListView)

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("slots/generate/", GenerateWeeklySlotsView.as_view(), name="admin_generate_slots"),
    path("slots/clear/", ClearSlotsView.as_view(), name="admin_clear_slots"),
    path("tables/", TableListView.as_view(), name="admin_tables"),
    path("tables/<int:pk>/edit/", TableUpdateView.as_view(), name="admin_table_edit"),
    path("settings/", CafeSettingsView.as_view(), name="admin_settings"),
    path("discounts/", DiscountListView.as_view(), name="admin_discounts"),
]