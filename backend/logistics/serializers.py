from rest_framework import serializers
from .models import Vehicle, DeliveryRoute, DeliveryStop, DeliveryItem, FleetMaintenance

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ('organization',)

class DeliveryStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryStop
        fields = '__all__'

class DeliveryRouteSerializer(serializers.ModelSerializer):
    stops = DeliveryStopSerializer(many=True, read_only=True)
    
    class Meta:
        model = DeliveryRoute
        fields = '__all__'
        read_only_fields = ('organization',)

class DeliveryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryItem
        fields = '__all__'

class FleetMaintenanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FleetMaintenance
        fields = '__all__'