from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, AttendanceViewSet, LeaveRequestViewSet, PayrollViewSet

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employee')
router.register('attendance', AttendanceViewSet, basename='attendance')
router.register('leave-requests', LeaveRequestViewSet, basename='leave-request')
router.register('payroll', PayrollViewSet, basename='payroll')

urlpatterns = [
    path('', include(router.urls)),
]