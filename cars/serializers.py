from rest_framework import serializers
from .models import Car


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = ['id', 'car_model', 'license_start', 'license_end']
        read_only_fields = ['id']
