from django.db import models
from decimal import Decimal
from django.utils import timezone


class Car(models.Model):
    car_model = models.CharField(max_length=255, help_text="Car model and brand")
    license_start = models.DateField(help_text="License start date")
    license_end = models.DateField(help_text="License expiration date")
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Car'
        verbose_name_plural = 'Cars'
    
    def __str__(self):
        return f"{self.car_model} (License: {self.license_start} to {self.license_end})"


class DailyEntry(models.Model):
    """Daily operational data for a car."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='daily_entries')
    inspection_date = models.DateField()
    day_name = models.CharField(max_length=16)
    driver_name = models.CharField(max_length=255)
    area = models.CharField(max_length=255, blank=True, default='')

    # Monetary fields (defaults to 0)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    default_freight = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Alternative freight bucket that is not added to normal freight totals")
    gas = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    oil = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    card = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    fines = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tips = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    maintenance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    spare_parts = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tires = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    washing = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    # New generic daily expense
    without = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Additional unspecified expense to include in totals")

    week_start = models.DateField(help_text="Saturday date for the week this entry belongs to")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["car", "week_start"]),
            models.Index(fields=["inspection_date"]),
        ]
        ordering = ["-inspection_date", "car_id"]

    def save(self, *args, **kwargs):
        # Ensure week_start is set based on inspection_date (week Sat-Fri)
        if not self.week_start and self.inspection_date:
            self.week_start = week_start_from_date(self.inspection_date)
        if not self.day_name and self.inspection_date:
            self.day_name = self.inspection_date.strftime('%A')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"DailyEntry car={self.car_id} date={self.inspection_date}"


class WeeklySummary(models.Model):
    """Weekly data per car. Net fields are computed from daily entries for the week."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='weekly_summaries')
    week_start = models.DateField(help_text="Saturday date (week start)")
    week_end = models.DateField(help_text="Friday date (week end)")

    odometer_start = models.PositiveIntegerField()
    odometer_end = models.PositiveIntegerField()

    driver_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    custody = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True, default='')

    net_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    default_net_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("car", "week_start")
        indexes = [
            models.Index(fields=["car", "week_start"]),
        ]
        ordering = ["-week_start", "car_id"]

    def save(self, *args, **kwargs):
        from django.db.models import Sum
        # Compute or fix week_end to be Friday of the same week as week_start
        if self.week_start and (not self.week_end or self.week_end == self.week_start or self.week_end < self.week_start):
            self.week_end = self.week_start + timedelta(days=6)
        # Aggregate daily totals for the week
        qs = DailyEntry.objects.filter(car=self.car, week_start=self.week_start)
        totals = qs.aggregate(
            freight=Sum('freight'), default_freight=Sum('default_freight'), gas=Sum('gas'), oil=Sum('oil'), card=Sum('card'),
            fines=Sum('fines'), tips=Sum('tips'), maintenance=Sum('maintenance'),
            spare_parts=Sum('spare_parts'), tires=Sum('tires'), balance=Sum('balance'),
            washing=Sum('washing'), without=Sum('without')
        )
        def d(x):
            return totals.get(x) or Decimal('0.00')
        expenses = (
            d('gas') + d('oil') + d('card') + d('fines') + d('tips') +
            d('maintenance') + d('spare_parts') + d('tires') + d('balance') + d('washing') + d('without')
        )
        # Include driver salary in weekly expenses
        driver_salary = self.driver_salary or Decimal('0.00')
        expenses = expenses + driver_salary
        total_freight = d('freight')
        default_total_freight = d('default_freight')
        self.net_expenses = expenses
        self.net_revenue = total_freight + (self.custody or Decimal('0.00')) - expenses
        # default_net_revenue uses default_freight totals instead of freight
        self.default_net_revenue = default_total_freight + (self.custody or Decimal('0.00')) - expenses
        super().save(*args, **kwargs)


# Helpers
from datetime import timedelta

def week_start_from_date(d):
    """Return Saturday date for the week containing d (week Sat-Fri)."""
    weekday = d.weekday()  # Mon=0 .. Sun=6
    # Saturday is 5
    delta = (weekday - 5) % 7
    return d - timedelta(days=delta)


class MaintenanceEntry(models.Model):
    """Vehicle maintenance record (year-round), monetary fields per entry."""
    car = models.ForeignKey('cars.Car', on_delete=models.CASCADE, related_name='maintenance_entries')
    date = models.DateField()

    air_filter = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    oil_filter = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gas_filter = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    oil_change = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    spare_part_type = models.CharField(max_length=255, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'id']
        indexes = [
            models.Index(fields=['car', 'date']),
        ]

    def __str__(self):
        return f"MaintenanceEntry car={self.car_id} date={self.date}"
