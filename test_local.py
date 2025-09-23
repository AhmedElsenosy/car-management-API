#!/usr/bin/env python
"""
Quick test script to verify the Car Management API is working locally
Run this before deploying to Render
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from cars.models import Car
from datetime import date

def test_database():
    """Test database operations"""
    print("🔍 Testing Database Operations...")
    
    # Clean up any existing test data
    Car.objects.filter(car_model__startswith="TEST_").delete()
    
    # Create a test car
    test_car = Car.objects.create(
        car_model="TEST_Toyota Camry 2024",
        license_start=date(2024, 1, 1),
        license_end=date(2025, 1, 1)
    )
    print(f"✅ Created car: {test_car}")
    
    # Read the car
    retrieved_car = Car.objects.get(id=test_car.id)
    print(f"✅ Retrieved car: {retrieved_car}")
    
    # Update the car
    retrieved_car.car_model = "TEST_Toyota Camry 2024 Updated"
    retrieved_car.save()
    print(f"✅ Updated car: {retrieved_car}")
    
    # List all cars
    all_cars = Car.objects.all()
    print(f"✅ Total cars in database: {all_cars.count()}")
    
    # Delete the test car
    test_car.delete()
    print("✅ Deleted test car")
    
    print("\n✅ All database operations working correctly!")
    return True

def check_settings():
    """Check Django settings"""
    from django.conf import settings
    
    print("\n📋 Current Settings:")
    print(f"   Database: {'SQLite' if 'sqlite' in settings.DATABASES['default']['ENGINE'] else 'PostgreSQL'}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Static URL: {settings.STATIC_URL}")
    print(f"   Allowed Hosts: {settings.ALLOWED_HOSTS}")

if __name__ == "__main__":
    print("=" * 50)
    print("🚗 Car Management API - Local Test")
    print("=" * 50)
    
    try:
        check_settings()
        test_database()
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Your project is ready for deployment.")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please fix the error before deploying.")
        sys.exit(1)