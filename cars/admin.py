from django.contrib import admin
from .models import Car, DailyEntry, WeeklySummary, MaintenanceEntry

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ("id", "car_model", "license_start", "license_end")
    search_fields = ("car_model",)

@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "inspection_date", "driver_name", "freight", "without")
    list_filter = ("car", "week_start")
    search_fields = ("driver_name", "area")

@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "week_start", "odometer_start", "odometer_end", "net_revenue", "default_net_revenue")
    list_filter = ("car", "week_start")
    search_fields = ("description",)

@admin.register(MaintenanceEntry)
class MaintenanceEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "car", "date", "spare_part_type", "air_filter", "oil_filter", "gas_filter", "oil_change", "price")
    list_filter = ("car", "date")
    search_fields = ("spare_part_type",)
