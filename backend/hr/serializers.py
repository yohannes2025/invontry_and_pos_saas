from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Employee, Attendance, LeaveRequest, Payroll

User = get_user_model()

class EmployeeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Employee
        fields = '__all__'
        read_only_fields = ('organization', 'employee_id')
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    
    def get_email(self, obj):
        return obj.user.email

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payroll
        fields = '__all__'
        read_only_fields = ('created_at',)
    
    def get_employee_name(self, obj):
        return obj.employee.user.get_full_name()