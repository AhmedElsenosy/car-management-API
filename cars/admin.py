from django.contrib import admin
from .models import Car, DailyEntry, WeeklySummary

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("id", "car_model", "license_start", "license_end")
    search_fields = ("car_model",)

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "inspection_date", "driver_name", "freight")
    list_filter = ("car", "week_start")
    search_fields = ("driver_name", "area")

@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "week_start", "odometer_start", "odometer_end", "net_revenue")
    list_filter = ("car", "week_start")
