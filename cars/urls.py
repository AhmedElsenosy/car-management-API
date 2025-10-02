from django.urls import path
from . import views

urlpatterns = [
    path('cars/', views.car_list_create, name='car-list-create'),
    path('cars/<int:pk>/', views.car_detail, name='car-detail'),

    # Daily & weekly endpoints
    path('daily-entries/', views.create_daily_entry, name='create-daily-entry'),
    path('weekly/', views.create_weekly_summary, name='create-weekly-summary'),
    path('weekly/detail/', views.get_weekly_detail, name='get-weekly-detail'),
]
