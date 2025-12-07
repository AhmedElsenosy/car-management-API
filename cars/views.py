from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Car, DailyEntry, WeeklySummary, week_start_from_date
from .serializers import (
    CarSerializer,
    DailyEntrySerializer,
    WeeklyCreateSerializer,
    WeeklyDetailSerializer,
    MonthlyDetailSerializer,
    MaintenanceEntrySerializer,
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
            'perished': serializer.validated_data.get('perished') or 0,
            'description': serializer.validated_data.get('description', ''),
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
        # Create an in-memory summary object for this response only (do not save)
        summary = WeeklySummary(
            car=car,
            week_start=ws,
            week_end=ws + timedelta(days=6),
            odometer_start=0,
            odometer_end=0,
            driver_salary=0,
            custody=0,
            perished=0,
            description='',
        )
    else:
        # Fix existing rows that have incorrect or missing week_end
        if not summary.week_end or summary.week_end == ws or summary.week_end < ws:
            summary.week_end = ws + timedelta(days=6)
            summary.save(update_fields=["week_end"])
    payload = _build_weekly_payload(summary)
    return Response(WeeklyDetailSerializer(payload).data)


# Monthly maintenance table endpoint
@api_view(['GET'])
def get_maintenance_month(request):
    """
    GET /api/maintenance/month/?car_id=<id>&year=YYYY&month=MM
    Returns all maintenance entries for the car in that specific month, plus monthly totals.
    Money fields: air_filter, oil_filter, gas_filter, oil_change, price
    full_total = sum of those totals.
    """
    car_id = request.query_params.get('car_id')
    year = request.query_params.get('year')
    month = request.query_params.get('month')
    if not car_id or not year or not month:
        return Response({'detail': 'car_id, year and month are required query params'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        car = Car.objects.get(pk=int(car_id))
        y = int(year)
        m = int(month)
        if not (1 <= m <= 12):
            raise ValueError('Month must be 1-12')
    except Exception:
        return Response({'detail': 'Invalid car_id/year/month'}, status=status.HTTP_400_BAD_REQUEST)

    from .models import MaintenanceEntry
    entries = MaintenanceEntry.objects.filter(car=car, date__year=y, date__month=m).order_by('date', 'id')
    
    # Get all entries for the year (for yearly totals)
    yearly_entries = MaintenanceEntry.objects.filter(car=car, date__year=y)

    # Totals calculation function
    def sum_qs(qs):
        agg = qs.aggregate(
            air_filter=Sum('air_filter'), oil_filter=Sum('oil_filter'), gas_filter=Sum('gas_filter'),
            oil_change=Sum('oil_change'), price=Sum('price')
        )
        # normalize None to 0
        for k in list(agg.keys()):
            agg[k] = agg[k] or 0
        agg['full_total'] = (agg['air_filter'] or 0) + (agg['oil_filter'] or 0) + (agg['gas_filter'] or 0) + (agg['oil_change'] or 0) + (agg['price'] or 0)
        return agg

    monthly_totals = sum_qs(entries)
    yearly_totals = sum_qs(yearly_entries)

    # Serialize entries
    entries_data = MaintenanceEntrySerializer(entries, many=True).data

    payload = {
        'car_id': car.id,
        'year': y,
        'month': m,
        'entries': entries_data,
        'monthly_totals': monthly_totals,
        'yearly_totals': yearly_totals,
    }
    return Response(payload)


# Monthly detail endpoint
@api_view(['GET'])
def get_monthly_detail(request):
    """
    GET /api/monthly/detail/?car_id=<id>&year=YYYY&month=MM
    Returns a monthly summary built from weekly summaries and daily entries in that month.
    - odometer_start: from the first weekly summary in the month (odometer_start)
    - odometer_end: from the last weekly summary in the month (odometer_end)
    - distance_total: sum of weekly distances (max(0, end-start) per week)
    - gas_total: sum of gas across all daily entries in the month
    - gas_per_km: gas_total / distance_total (0 if distance_total==0)
    - driver_salary_total, custody_total: sums from weekly summaries
    - net_expenses_total, net_revenue_total, default_net_revenue_total: sums from weekly summaries
    """
    car_id = request.query_params.get('car_id')
    year = request.query_params.get('year')
    month = request.query_params.get('month')
    if not car_id or not year or not month:
        return Response({'detail': 'car_id, year and month are required query params'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        car = Car.objects.get(pk=int(car_id))
        y = int(year)
        m = int(month)
        if not (1 <= m <= 12):
            raise ValueError
    except Exception:
        return Response({'detail': 'Invalid car_id/year/month'}, status=status.HTTP_400_BAD_REQUEST)

    # Compute month start/end
    from datetime import date
    if m == 12:
        period_start = date(y, m, 1)
        period_end = date(y + 1, 1, 1) - timedelta(days=1)
    else:
        period_start = date(y, m, 1)
        period_end = date(y, m + 1, 1) - timedelta(days=1)

    # Weekly summaries that start in this month
    week_qs = WeeklySummary.objects.filter(car=car, week_start__gte=period_start, week_start__lte=period_end).order_by('week_start')

    # Daily entries in this calendar month
    daily_qs = DailyEntry.objects.filter(car=car, inspection_date__gte=period_start, inspection_date__lte=period_end)

    # Aggregates from daily - get all expense fields
    daily_aggs = daily_qs.aggregate(
        freight=Sum('freight'), default_freight=Sum('default_freight'),
        gas=Sum('gas'), oil=Sum('oil'), card=Sum('card'), fines=Sum('fines'), tips=Sum('tips'),
        maintenance=Sum('maintenance'), spare_parts=Sum('spare_parts'), tires=Sum('tires'),
        balance=Sum('balance'), washing=Sum('washing'), without=Sum('without')
    )
    # Normalize all to Decimal
    def daily_dec(k):
        return Decimal(str(daily_aggs.get(k) or 0))
    
    gas_total = daily_dec('gas')

    # Distance and odometers from weekly
    distance_total = 0
    odo_start = 0
    odo_end = 0
    driver_salary_total = Decimal('0')
    custody_total = Decimal('0')
    perished_total = Decimal('0')
    net_expenses_total = Decimal('0')
    net_revenue_total = Decimal('0')
    default_net_revenue_total = Decimal('0')
    net_driver_total = Decimal('0')
    net_car_total = Decimal('0')

    weeks_list = []
    for idx, wk in enumerate(week_qs):
        if idx == 0:
            odo_start = int(wk.odometer_start or 0)
        odo_end = int(wk.odometer_end or 0)
        dist = max(0, int((wk.odometer_end or 0) - (wk.odometer_start or 0)))
        distance_total += dist

        # Recompute weekly totals dynamically from daily entries in that week (do not trust stored net fields)
        dqs = DailyEntry.objects.filter(car=car, week_start=wk.week_start)
        daggs = dqs.aggregate(
            freight=Sum('freight'), default_freight=Sum('default_freight'),
            gas=Sum('gas'), oil=Sum('oil'), card=Sum('card'), fines=Sum('fines'), tips=Sum('tips'),
            maintenance=Sum('maintenance'), spare_parts=Sum('spare_parts'), tires=Sum('tires'),
            balance=Sum('balance'), washing=Sum('washing'), without=Sum('without')
        )
        def decv(k):
            return Decimal(str(daggs.get(k) or 0))
        weekly_expenses = (
            decv('gas') + decv('oil') + decv('card') + decv('fines') + decv('tips') +
            decv('maintenance') + decv('spare_parts') + decv('tires') + decv('balance') + decv('washing') + decv('without')
        ) + Decimal(str(wk.driver_salary or 0))
        weekly_freight = decv('freight')
        weekly_default_freight = decv('default_freight')
        weekly_custody = Decimal(str(wk.custody or 0))
        weekly_perished = Decimal(str(wk.perished or 0))
        weekly_driver_salary = Decimal(str(wk.driver_salary or 0))
        weekly_net = weekly_freight + weekly_custody - weekly_expenses
        weekly_default_net = weekly_default_freight + weekly_custody - weekly_expenses
        
        # Calculate net_driver and net_car for this week
        daily_expenses_only = weekly_expenses - weekly_driver_salary
        weekly_net_driver = weekly_freight + weekly_custody - daily_expenses_only
        weekly_net_car = weekly_freight + weekly_default_freight - (daily_expenses_only + weekly_driver_salary + weekly_perished)

        driver_salary_total += weekly_driver_salary
        custody_total += weekly_custody
        perished_total += weekly_perished
        net_expenses_total += weekly_expenses
        net_revenue_total += weekly_net
        default_net_revenue_total += weekly_default_net
        net_driver_total += weekly_net_driver
        net_car_total += weekly_net_car

        weeks_list.append({
            'week_start': wk.week_start,
            'week_end': wk.week_end,
            'odometer_start': wk.odometer_start,
            'odometer_end': wk.odometer_end,
            'distance': dist,
            'driver_salary': wk.driver_salary,
            'custody': wk.custody,
            'perished': wk.perished,
            'net_expenses': weekly_expenses,
            'net_revenue': weekly_net,
            'default_net_revenue': weekly_default_net,
            'net_driver': weekly_net_driver,
            'net_car': weekly_net_car,
        })

    gas_per_km = Decimal('0')
    if distance_total > 0:
        gas_per_km = (gas_total / Decimal(distance_total)).quantize(Decimal('0.0001'))

    # Build daily totals dict from aggregated daily entries
    daily_totals = {
        'freight': daily_dec('freight'),
        'default_freight': daily_dec('default_freight'),
        'gas': daily_dec('gas'),
        'oil': daily_dec('oil'),
        'card': daily_dec('card'),
        'fines': daily_dec('fines'),
        'tips': daily_dec('tips'),
        'maintenance': daily_dec('maintenance'),
        'spare_parts': daily_dec('spare_parts'),
        'tires': daily_dec('tires'),
        'balance': daily_dec('balance'),
        'washing': daily_dec('washing'),
        'without': daily_dec('without'),
    }
    
    payload = {
        'car_id': car.id,
        'year': y,
        'month': m,
        'period_start': period_start,
        'period_end': period_end,
        'odometer_start': odo_start,
        'odometer_end': odo_end,
        'distance_total': distance_total,
        'gas_total': gas_total,
        'gas_per_km': gas_per_km,
        'driver_salary_total': driver_salary_total,
        'custody_total': custody_total,
        'perished_total': perished_total,
        'net_expenses_total': net_expenses_total,
        'net_revenue_total': net_revenue_total,
        'default_net_revenue_total': default_net_revenue_total,
        'net_driver_total': net_driver_total,
        'net_car_total': net_car_total,
        'daily_totals': daily_totals,
        'weeks': weeks_list,
    }
    return Response(MonthlyDetailSerializer(payload).data)


# Maintenance endpoints
@api_view(['POST'])
def create_maintenance_entry(request):
    """Create a maintenance record for a car (for a specific date)."""
    serializer = MaintenanceEntrySerializer(data=request.data)
    if serializer.is_valid():
        obj = serializer.save()
        return Response(MaintenanceEntrySerializer(obj).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT', 'PATCH'])
def update_maintenance_by_date(request):
    """Update a maintenance record identified by (car_id, date)."""
    car_id = request.data.get('car_id')
    date_str = request.data.get('date')
    if not car_id or not date_str:
        return Response({'detail': 'car_id and date are required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ref_date = datetime.strptime(str(date_str), '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'date must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    from .models import MaintenanceEntry
    qs = MaintenanceEntry.objects.filter(car_id=car_id, date=ref_date)
    count = qs.count()
    if count == 0:
        return Response({'detail': 'No maintenance entry found for this car and date.'}, status=status.HTTP_404_NOT_FOUND)
    if count > 1:
        return Response({'detail': 'Multiple maintenance entries found for this car and date. Please update by ID.'}, status=status.HTTP_400_BAD_REQUEST)

    obj = qs.first()
    serializer = MaintenanceEntrySerializer(obj, data=request.data, partial=True)
    if serializer.is_valid():
        obj = serializer.save()
        return Response(MaintenanceEntrySerializer(obj).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Update daily entry by car and date
@api_view(['PUT', 'PATCH'])
def update_daily_entry_by_date(request):
    """
    Update a daily entry identified by (car_id, inspection_date).
    - Body must include car_id and inspection_date.
    - Other fields are optional; partial update is supported.
    """
    car_id = request.data.get('car_id')
    inspection_date = request.data.get('inspection_date')
    if not car_id or not inspection_date:
        return Response({'detail': 'car_id and inspection_date are required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ref_date = datetime.strptime(str(inspection_date), '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'inspection_date must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    qs = DailyEntry.objects.filter(car_id=car_id, inspection_date=ref_date)
    count = qs.count()
    if count == 0:
        return Response({'detail': 'No daily entry found for this car and date.'}, status=status.HTTP_404_NOT_FOUND)
    if count > 1:
        return Response({'detail': 'Multiple daily entries found for this car and date. Please update by ID.'}, status=status.HTTP_400_BAD_REQUEST)

    entry = qs.first()
    serializer = DailyEntrySerializer(entry, data=request.data, partial=True)
    if serializer.is_valid():
        entry = serializer.save()
        return Response(DailyEntrySerializer(entry).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Update weekly summary by week_ref_date (any date within the week)
@api_view(['PUT', 'PATCH'])
def update_weekly_by_date(request):
    """
    Update a weekly summary identified by (car_id, week_ref_date inside target week).
    - Body must include car_id and week_ref_date.
    - Updates any provided fields among odometer_start, odometer_end, driver_salary, custody, description.
    - Returns the refreshed weekly detail payload.
    """
    car_id = request.data.get('car_id')
    week_ref_date = request.data.get('week_ref_date')
    if not car_id or not week_ref_date:
        return Response({'detail': 'car_id and week_ref_date are required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        ref = datetime.strptime(str(week_ref_date), '%Y-%m-%d').date()
    except ValueError:
        return Response({'detail': 'week_ref_date must be YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

    ws = week_start_from_date(ref)
    try:
        summary = WeeklySummary.objects.get(car_id=car_id, week_start=ws)
    except WeeklySummary.DoesNotExist:
        return Response({'detail': 'Weekly summary not found for this car and week.'}, status=status.HTTP_404_NOT_FOUND)

    # Update allowed fields if provided
    for field in ['odometer_start', 'odometer_end', 'driver_salary', 'custody', 'perished', 'description']:
        if field in request.data:
            setattr(summary, field, request.data.get(field))

    # Ensure correct week_end and recompute net fields
    summary.week_end = ws + timedelta(days=6)
    summary.save()  # save() recomputes net_expenses / net_revenue

    payload = _build_weekly_payload(summary)
    return Response(WeeklyDetailSerializer(payload).data)


def _build_weekly_payload(summary: WeeklySummary):
    """Utility: build response dict for WeeklyDetailSerializer."""
    ws = summary.week_start
    entries = DailyEntry.objects.filter(car=summary.car, week_start=ws).order_by('inspection_date')
    # Aggregate column totals
    aggs = entries.aggregate(
        freight=Sum('freight'), default_freight=Sum('default_freight'), gas=Sum('gas'), oil=Sum('oil'), card=Sum('card'),
        fines=Sum('fines'), tips=Sum('tips'), maintenance=Sum('maintenance'),
        spare_parts=Sum('spare_parts'), tires=Sum('tires'), balance=Sum('balance'),
        washing=Sum('washing'), without=Sum('without')
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
        dec(aggs.get('tires')) + dec(aggs.get('balance')) + dec(aggs.get('washing')) + dec(aggs.get('without'))
    ) + dec(summary.driver_salary)
    total_freight = dec(aggs.get('freight'))
    default_total_freight = dec(aggs.get('default_freight'))
    custody_dec = dec(summary.custody)
    perished_dec = dec(summary.perished)
    driver_salary_dec = dec(summary.driver_salary)
    
    net_expenses = expenses
    net_revenue = total_freight + custody_dec - expenses
    default_net_revenue = default_total_freight + custody_dec - expenses
    
    # Daily expenses only (without driver_salary)
    daily_expenses_only = expenses - driver_salary_dec
    
    # net_driver = (freight + custody) - daily_expenses_only (NO driver_salary)
    net_driver = total_freight + custody_dec - daily_expenses_only
    
    # net_car = (freight + default_freight) - (daily_expenses_only + driver_salary + perished)
    net_car = total_freight + default_total_freight - (daily_expenses_only + driver_salary_dec + perished_dec)

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
        'perished': summary.perished,
        'description': summary.description,
        'net_expenses': net_expenses,
        'net_revenue': net_revenue,
        'default_net_revenue': default_net_revenue,
        'net_driver': net_driver,
        'net_car': net_car,
        'totals': aggs,
        'daily_entries': DailyEntrySerializer(entries, many=True).data,
    }
