from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from datetime import datetime
from decimal import Decimal

from .models import Car, DailyEntry, WeeklySummary, week_start_from_date
from .serializers import (
    CarSerializer,
    DailyEntrySerializer,
    WeeklyCreateSerializer,
    WeeklyDetailSerializer,
)


@api_view(['GET', 'POST'])
def car_list_create(request):
    """
    GET: Get all cars
    POST: Create a new car
    """
    if request.method == 'GET':
        cars = Car.objects.all()
        serializer = CarSerializer(cars, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CarSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def car_detail(request, pk):
    """
    GET: Get car by id
    PUT: Update car by id
    DELETE: Delete car by id
    """
    try:
        car = Car.objects.get(pk=pk)
    except Car.DoesNotExist:
        return Response({'error': 'Car not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CarSerializer(car)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = CarSerializer(car, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        car.delete()
        return Response({'message': 'Car deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


# Daily entry endpoint
@api_view(['POST'])
def create_daily_entry(request):
    """Create a daily entry for a car. Week is auto-calculated (Sat-Fri)."""
    serializer = DailyEntrySerializer(data=request.data)
    if serializer.is_valid():
        entry = serializer.save()
        return Response(DailyEntrySerializer(entry).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Weekly creation endpoint
@api_view(['POST'])
def create_weekly_summary(request):
    """
    Create or update a weekly summary for a car. Provide:
    - car_id
    - week_ref_date (any date inside the target week)
    - odometer_start, odometer_end, driver_salary, custody
    Net fields are computed from daily entries in that week: 
    net_expenses = sum(all daily money except freight)
    net_revenue = (sum freight + custody) - net_expenses
    """
    serializer = WeeklyCreateSerializer(data=request.data)
    if serializer.is_valid():
        car = serializer.validated_data['car']
        week_start = serializer.validated_data['week_start']
        defaults = {
            'odometer_start': serializer.validated_data['odometer_start'],
            'odometer_end': serializer.validated_data['odometer_end'],
            'driver_salary': serializer.validated_data.get('driver_salary') or 0,
            'custody': serializer.validated_data.get('custody') or 0,
        }
        obj, _created = WeeklySummary.objects.update_or_create(
            car=car, week_start=week_start,
            defaults=defaults
        )
        # save() computes net fields
        obj.save()
        data = WeeklyDetailSerializer(_build_weekly_payload(obj)).data
        return Response(data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Weekly detail endpoint
@api_view(['GET'])
def get_weekly_detail(request):
    """
    GET /api/weekly/detail/?car_id=<id>&date=YYYY-MM-DD
    date can be any date within the target week (Sat-Fri)
    """
    car_id = request.query_params.get('car_id')
    date_str = request.query_params.get('date')
    if not car_id or not date_str:
        return Response({'detail': 'car_id and date are required query params'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        car = Car.objects.get(pk=int(car_id))
    except (ValueError, Car.DoesNotExist):
        return Response({'detail': 'Invalid car_id'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ref_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'date must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    ws = week_start_from_date(ref_date)
    summary = WeeklySummary.objects.filter(car=car, week_start=ws).first()
    if not summary:
        # create a temporary summary-like object to surface numbers even if weekly row not created yet
        summary = WeeklySummary(car=car, week_start=ws, week_end=ws)
        summary.odometer_start = 0
        summary.odometer_end = 0
        summary.driver_salary = 0
        summary.custody = 0
        summary.save()
    payload = _build_weekly_payload(summary)
    return Response(WeeklyDetailSerializer(payload).data)


def _build_weekly_payload(summary: WeeklySummary):
    """Utility: build response dict for WeeklyDetailSerializer."""
    ws = summary.week_start
    entries = DailyEntry.objects.filter(car=summary.car, week_start=ws).order_by('inspection_date')
    # Aggregate column totals
    aggs = entries.aggregate(
        freight=Sum('freight'), gas=Sum('gas'), oil=Sum('oil'), card=Sum('card'),
        fines=Sum('fines'), tips=Sum('tips'), maintenance=Sum('maintenance'),
        spare_parts=Sum('spare_parts'), tires=Sum('tires'), balance=Sum('balance'),
        washing=Sum('washing')
    )
    for k in list(aggs.keys()):
        aggs[k] = aggs[k] or 0

    # Compute distance and gas_per_km
    try:
        distance = max(0, int((summary.odometer_end or 0) - (summary.odometer_start or 0)))
    except Exception:
        distance = 0
    gas_total = Decimal(str(aggs.get('gas', 0)))
    gas_per_km = Decimal('0')
    if distance > 0:
        gas_per_km = (gas_total / Decimal(distance)).quantize(Decimal('0.0001'))

    # Dynamically recompute weekly net values so new daily entries are reflected immediately
    def dec(v):
        return Decimal(str(v or 0))
    expenses = (
        dec(aggs.get('gas')) + dec(aggs.get('oil')) + dec(aggs.get('card')) + dec(aggs.get('fines')) +
        dec(aggs.get('tips')) + dec(aggs.get('maintenance')) + dec(aggs.get('spare_parts')) +
        dec(aggs.get('tires')) + dec(aggs.get('balance')) + dec(aggs.get('washing'))
    ) + dec(summary.driver_salary)
    total_freight = dec(aggs.get('freight'))
    custody_dec = dec(summary.custody)
    net_expenses = expenses
    net_revenue = total_freight + custody_dec - expenses

    return {
        'car_id': summary.car.id,
        'week_start': summary.week_start,
        'week_end': summary.week_end,
        'odometer_start': summary.odometer_start,
        'odometer_end': summary.odometer_end,
        'distance': distance,
        'gas_per_km': gas_per_km,
        'driver_salary': summary.driver_salary,
        'custody': summary.custody,
        'net_expenses': net_expenses,
        'net_revenue': net_revenue,
        'totals': aggs,
        'daily_entries': DailyEntrySerializer(entries, many=True).data,
    }
