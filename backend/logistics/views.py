from rest_framework import viewsets, generics, permissions, response, status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Vehicle, DeliveryRoute, DeliveryStop, DeliveryItem, FleetMaintenance
from .serializers import (
    VehicleSerializer, DeliveryRouteSerializer, DeliveryStopSerializer,
    DeliveryItemSerializer, FleetMaintenanceSerializer
)
from tenants.models import Organization

def get_org(request):
    org_slug = request.headers.get('X-Org-Slug')
    return Organization.objects.get(slug=org_slug)

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return Vehicle.objects.filter(organization=org)
    
    def perform_create(self, serializer):
        org = get_org(self.request)
        serializer.save(organization=org)
    
    @action(detail=True, methods=['post'])
    def assign_driver(self, request, pk=None):
        vehicle = self.get_object()
        driver_id = request.data.get('driver_id')
        if not driver_id:
            return response.Response(
                {'error': 'driver_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        vehicle.assigned_driver_id = driver_id
        vehicle.save()
        return response.Response(VehicleSerializer(vehicle).data)
    
    @action(detail=True, methods=['get'])
    def location_history(self, request, pk=None):
        vehicle = self.get_object()
        # Implement GPS tracking history
        return response.Response({
            'vehicle': vehicle.license_plate,
            'locations': [
                {'lat': vehicle.current_location_lat, 'lng': vehicle.current_location_lng}
            ]
        })

class DeliveryRouteViewSet(viewsets.ModelViewSet):
    serializer_class = DeliveryRouteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return DeliveryRoute.objects.filter(organization=org)
    
    def perform_create(self, serializer):
        org = get_org(self.request)
        serializer.save(organization=org)
    
    @action(detail=True, methods=['post'])
    def start_route(self, request, pk=None):
        route = self.get_object()
        if route.status != 'planned':
            return response.Response(
                {'error': 'Route is not in planned state'},
                status=status.HTTP_400_BAD_REQUEST
            )
        route.status = 'in_progress'
        route.start_time = timezone.now()
        route.save()
        return response.Response(DeliveryRouteSerializer(route).data)
    
    @action(detail=True, methods=['post'])
    def complete_stop(self, request, pk=None):
        route = self.get_object()
        stop_id = request.data.get('stop_id')
        stop = get_object_or_404(DeliveryStop, id=stop_id, route=route)
        stop.status = 'completed'
        stop.actual_time = timezone.now()
        stop.save()
        route.completed_stops += 1
        route.save()
        
        # Process delivery items
        for item in stop.items.all():
            item.is_delivered = True
            item.save()
        
        return response.Response(DeliveryStopSerializer(stop).data)
    
    @action(detail=True, methods=['post'])
    def add_stop(self, request, pk=None):
        route = self.get_object()
        serializer = DeliveryStopSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(route=route)
            route.total_stops += 1
            route.save()
            return response.Response(serializer.data, status=status.HTTP_201_CREATED)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FleetMaintenanceViewSet(viewsets.ModelViewSet):
    serializer_class = FleetMaintenanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return FleetMaintenance.objects.filter(vehicle__organization=org)