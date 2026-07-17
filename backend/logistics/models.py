from django.db import models
from django.contrib.auth import get_user_model
from tenants.models import Organization
from catalog.models import Product
from inventory.models import Workspace

User = get_user_model()

class Vehicle(models.Model):
    VEHICLE_TYPES = [
        ('van', 'Van'),
        ('truck', 'Truck'),
        ('refrigerated', 'Refrigerated Truck'),
        ('bike', 'Cargo Bike'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    license_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    current_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_vehicles')
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.license_plate}"

class DeliveryRoute(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='routes')
    route_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_distance_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_stops = models.IntegerField(default=0)
    completed_stops = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class DeliveryStop(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('arrived', 'Arrived'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    route = models.ForeignKey(DeliveryRoute, on_delete=models.CASCADE, related_name='stops')
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_time = models.DateTimeField()
    actual_time = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    order_reference = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"Stop {self.id} - {self.route.route_name}"

class DeliveryItem(models.Model):
    stop = models.ForeignKey(DeliveryStop, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='pcs')
    is_delivered = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class FleetMaintenance(models.Model):
    MAINTENANCE_TYPES = [
        ('routine', 'Routine'),
        ('repair', 'Repair'),
        ('inspection', 'Inspection'),
    ]
    
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField()
    performed_by = models.CharField(max_length=255)
    next_due_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.date}"