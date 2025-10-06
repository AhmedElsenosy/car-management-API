from django.urls import path
from . import views

urlpatterns = [
    path('cars/', views.car_list_create, name='car-list-create'),
    path('cars/<int:pk>/', views.car_detail, name='car-detail'),

    # Daily & weekly endpoints
    path('daily-entries/', views.create_daily_entry, name='create-daily-entry'),
    path('weekly/', views.create_weekly_summary, name='create-weekly-summary'),
    path('weekly/detail/', views.get_weekly_detail, name='get-weekly-detail'),
    path('monthly/detail/', views.get_monthly_detail, name='get-monthly-detail'),

    # Update by date endpoints
    path('daily-entries/by-date/', views.update_daily_entry_by_date, name='update-daily-by-date'),
    path('weekly/by-date/', views.update_weekly_by_date, name='update-weekly-by-date'),

    # Maintenance
    path('maintenance/', views.create_maintenance_entry, name='create-maintenance'),
    path('maintenance/by-date/', views.update_maintenance_by_date, name='update-maintenance-by-date'),
    path('maintenance/year/', views.get_maintenance_year, name='maintenance-year'),
]
