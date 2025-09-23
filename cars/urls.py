from django.urls import path
from . import views

urlpatterns = [
    path('cars/', views.car_list_create, name='car-list-create'),
    path('cars/<int:pk>/', views.car_detail, name='car-detail'),
]
