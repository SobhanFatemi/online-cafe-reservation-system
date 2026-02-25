from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="index.html"), name="main_menu"), 
    path("accounts/", include("users.urls")),        
    path("accounts/", include("django.contrib.auth.urls")),
    path("menu/", include("menu.urls")),
    path("reservations/", include("reservations.urls")),
    path("admin-panel/", include("dashboard.urls")), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
