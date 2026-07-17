from rest_framework import viewsets, generics, permissions, response, status
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import Sum, Count
from decimal import Decimal
from .models import Employee, Attendance, LeaveRequest, Payroll
from .serializers import EmployeeSerializer, AttendanceSerializer, LeaveRequestSerializer, PayrollSerializer
from tenants.models import Organization

def get_org(request):
    org_slug = request.headers.get('X-Org-Slug')
    return Organization.objects.get(slug=org_slug)

class EmployeeViewSet(viewsets.ModelViewSet):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return Employee.objects.filter(organization=org, is_active=True)
    
    def perform_create(self, serializer):
        org = get_org(self.request)
        # Generate employee ID
        last_employee = Employee.objects.filter(organization=org).order_by('-id').first()
        next_id = 1 if not last_employee else last_employee.id + 1
        employee_id = f"EMP{str(next_id).zfill(5)}"
        serializer.save(organization=org, employee_id=employee_id)
    
    @action(detail=True, methods=['get'])
    def attendance_summary(self, request, pk=None):
        employee = self.get_object()
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        attendance = Attendance.objects.filter(
            employee=employee,
            date__gte=month_start
        )
        total_hours = attendance.aggregate(total=Sum('total_hours'))['total'] or 0
        total_overtime = attendance.aggregate(total=Sum('overtime_hours'))['total'] or 0
        
        return response.Response({
            'employee': employee.user.get_full_name(),
            'month': month_start.strftime('%B %Y'),
            'total_hours': float(total_hours),
            'total_overtime': float(total_overtime),
            'days_present': attendance.count(),
        })

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return Attendance.objects.filter(employee__organization=org)
    
    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        org = get_org(self.request)
        employee_id = request.data.get('employee_id')
        employee = Employee.objects.get(employee_id=employee_id, organization=org)
        
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': timezone.now()}
        )
        
        if not created:
            return response.Response(
                {'error': 'Already clocked in today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return response.Response(AttendanceSerializer(attendance).data)
    
    @action(detail=False, methods=['post'])
    def clock_out(self, request):
        org = get_org(self.request)
        employee_id = request.data.get('employee_id')
        employee = Employee.objects.get(employee_id=employee_id, organization=org)
        
        today = timezone.now().date()
        attendance = Attendance.objects.get(employee=employee, date=today, check_out__isnull=True)
        attendance.check_out = timezone.now()
        
        # Calculate hours
        duration = attendance.check_out - attendance.check_in
        attendance.total_hours = Decimal(str(duration.total_seconds() / 3600))
        
        # Calculate overtime (hours > 8)
        if attendance.total_hours > 8:
            attendance.overtime_hours = attendance.total_hours - 8
        
        attendance.save()
        
        return response.Response(AttendanceSerializer(attendance).data)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return LeaveRequest.objects.filter(employee__organization=org)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'approved'
        leave_request.approved_by = request.user
        leave_request.approved_at = timezone.now()
        leave_request.save()
        return response.Response(LeaveRequestSerializer(leave_request).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave_request = self.get_object()
        leave_request.status = 'rejected'
        leave_request.save()
        return response.Response(LeaveRequestSerializer(leave_request).data)

class PayrollViewSet(viewsets.ModelViewSet):
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return Payroll.objects.filter(employee__organization=org)
    
    @action(detail=False, methods=['post'])
    def generate_payroll(self, request):
        org = get_org(self.request)
        period_start = request.data.get('period_start')
        period_end = request.data.get('period_end')
        
        if not period_start or not period_end:
            return response.Response(
                {'error': 'period_start and period_end required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employees = Employee.objects.filter(organization=org, is_active=True)
        payroll_records = []
        
        for employee in employees:
            # Calculate attendance hours
            attendance_hours = Attendance.objects.filter(
                employee=employee,
                date__range=[period_start, period_end]
            ).aggregate(total=Sum('total_hours'))['total'] or 0
            
            overtime_hours = Attendance.objects.filter(
                employee=employee,
                date__range=[period_start, period_end]
            ).aggregate(total=Sum('overtime_hours'))['total'] or 0
            
            # Calculate base salary (monthly or hourly)
            if employee.employment_type == 'full_time':
                base_salary = employee.salary
            else:
                base_salary = float(attendance_hours) * float(employee.hourly_rate or 0)
            
            overtime_pay = float(overtime_hours) * float(employee.hourly_rate or 0) * 1.5
            tax_withheld = base_salary * Decimal('0.2')  # Simplified tax calculation
            
            net_pay = base_salary + overtime_pay - tax_withheld
            
            payroll = Payroll.objects.create(
                employee=employee,
                period_start=period_start,
                period_end=period_end,
                base_salary=base_salary,
                overtime_pay=overtime_pay,
                tax_withheld=tax_withheld,
                net_pay=net_pay,
            )
            payroll_records.append(payroll)
        
        return response.Response(PayrollSerializer(payroll_records, many=True).data)