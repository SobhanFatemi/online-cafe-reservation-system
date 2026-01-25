from django.contrib import admin
from .models import CafeTable, TimeSlot, WorkingHour

admin.site.register(CafeTable)
admin.site.register(TimeSlot)
admin.site.register(WorkingHour)