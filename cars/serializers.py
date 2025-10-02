from rest_framework import serializers
from .models import Car, DailyEntry, WeeklySummary, week_start_from_date
from decimal import Decimal
from datetime import timedelta


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'car_model', 'license_start', 'license_end']
        read_only_fields = ['id']


class DailyEntrySerializer(serializers.ModelSerializer):
    car_id = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all(), source='car', write_only=True)

    class Meta:
        model = DailyEntry
        fields = [
            'id', 'car_id', 'inspection_date', 'day_name', 'driver_name', 'area',
            'freight', 'gas', 'oil', 'card', 'fines', 'tips', 'maintenance',
            'spare_parts', 'tires', 'balance', 'washing', 'week_start'
        ]
        read_only_fields = ['id', 'week_start']

    def validate(self, attrs):
        # auto-compute week_start from inspection_date
        inspection_date = attrs.get('inspection_date')
        if inspection_date:
            attrs['week_start'] = week_start_from_date(inspection_date)
        # Default day_name from inspection_date if not provided
        if not attrs.get('day_name') and inspection_date:
            attrs['day_name'] = inspection_date.strftime('%A')
        return attrs


class WeeklyCreateSerializer(serializers.ModelSerializer):
    car_id = serializers.PrimaryKeyRelatedField(queryset=Car.objects.all(), source='car', write_only=True)
    week_ref_date = serializers.DateField(write_only=True, required=True, help_text="Any date inside the week (Saturday-Friday)")

    class Meta:
        model = WeeklySummary
        fields = [
            'id', 'car_id', 'week_ref_date', 'week_start', 'week_end',
            'odometer_start', 'odometer_end', 'driver_salary', 'custody',
            'net_expenses', 'net_revenue'
        ]
        read_only_fields = ['id', 'week_start', 'week_end', 'net_expenses', 'net_revenue']

    def validate(self, attrs):
        # Compute week_start/week_end from week_ref_date
        ref = attrs.pop('week_ref_date')
        ws = week_start_from_date(ref)
        attrs['week_start'] = ws
        attrs['week_end'] = ws + timedelta(days=6)
        return attrs


class WeeklyDetailSerializer(serializers.Serializer):
    """Aggregated weekly view combining totals and daily entries"""
    car_id = serializers.IntegerField()
    week_start = serializers.DateField()
    week_end = serializers.DateField()
    odometer_start = serializers.IntegerField()
    odometer_end = serializers.IntegerField()
    distance = serializers.IntegerField()
    gas_per_km = serializers.DecimalField(max_digits=12, decimal_places=4)
    driver_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    custody = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    totals = serializers.DictField()
    daily_entries = DailyEntrySerializer(many=True)
