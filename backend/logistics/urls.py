from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, DeliveryRouteViewSet, FleetMaintenanceViewSet

router = DefaultRouter()
router.register('vehicles', VehicleViewSet, basename='vehicle')
router.register('routes', DeliveryRouteViewSet, basename='route')
router.register('maintenance', FleetMaintenanceViewSet, basename='maintenance')

urlpatterns = [
    path('', include(router.urls)),
]