from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Car
from .serializers import CarSerializer


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
