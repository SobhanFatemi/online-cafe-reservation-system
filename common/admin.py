from django.contrib import admin

class BaseAdmin(admin.ModelAdmin):
    exclude = ("is_deleted",)