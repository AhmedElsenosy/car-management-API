
# Signal to automatically sync maintenance data to MaintenanceEntry
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender='cars.DailyEntry')
def sync_maintenance_entry(sender, instance, created, **kwargs):
    """
    Automatically create/update/delete MaintenanceEntry when DailyEntry is saved.
    - Copies maintenance amount to price
    - Copies WeeklySummary description to spare_part_type
    - Deletes MaintenanceEntry if maintenance becomes 0
    """
    # If maintenance is 0 or negative, delete any existing MaintenanceEntry
    if instance.maintenance <= Decimal('0.00'):
        MaintenanceEntry.objects.filter(
            car=instance.car,
            date=instance.inspection_date
        ).delete()
        return
    
    # If maintenance > 0, create or update MaintenanceEntry
    maintenance_entry, entry_created = MaintenanceEntry.objects.get_or_create(
        car=instance.car,
        date=instance.inspection_date,
        defaults={'price': instance.maintenance}
    )
    
    # Update price
    maintenance_entry.price = instance.maintenance
    
    # Get description from WeeklySummary for this week
    spare_part_description = ''
    try:
        weekly_summary = WeeklySummary.objects.get(
            car=instance.car,
            week_start=instance.week_start
        )
        if weekly_summary.description:
            spare_part_description = weekly_summary.description
    except WeeklySummary.DoesNotExist:
        # No WeeklySummary found, leave spare_part_type empty
        pass
    
    maintenance_entry.spare_part_type = spare_part_description
    maintenance_entry.save()
    
@receiver(post_save, sender='cars.WeeklySummary')
def update_maintenance_descriptions(sender, instance, created, **kwargs):
    """
    When WeeklySummary is created or updated, update all MaintenanceEntry records
    for that week with the description.
    """
    # Get all DailyEntry records for this car/week that have maintenance > 0
    daily_entries = DailyEntry.objects.filter(
        car=instance.car,
        week_start=instance.week_start,
        maintenance__gt=Decimal('0.00')
    )
    
    # Update the spare_part_type for each corresponding MaintenanceEntry
    for daily_entry in daily_entries:
        try:
            maintenance_entry = MaintenanceEntry.objects.get(
                car=daily_entry.car,
                date=daily_entry.inspection_date
            )
            maintenance_entry.spare_part_type = instance.description or ''
            maintenance_entry.save()
        except MaintenanceEntry.DoesNotExist:
            # Shouldn't happen, but skip if no MaintenanceEntry exists
            pass




from cars.models import MaintenanceEntry, WeeklySummary
from cars.models import week_start_from_date
for entry in MaintenanceEntry.objects.all():
    week_start = week_start_from_date(entry.date)
    try:
        ws = WeeklySummary.objects.get(car=entry.car, week_start=week_start)
        entry.spare_part_type = ws.description or ''
        entry.save()
    except WeeklySummary.DoesNotExist:
        pass