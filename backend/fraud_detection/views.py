from rest_framework import views, permissions, response, status
from rest_framework.decorators import api_view, permission_classes
from django.db import models
from .services import FraudDetectionService
from tenants.models import Organization
from pos.models import Sale
from inventory.models import StockMovement

def get_org(request):
    org_slug = request.headers.get('X-Org-Slug')
    return Organization.objects.get(slug=org_slug)

class FraudDetectionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        org = get_org(request)
        service = FraudDetectionService(org)
        
        days = int(request.query_params.get('days', 30))
        
        sales_anomalies = service.detect_sales_anomalies(days)
        inventory_anomalies = service.detect_inventory_anomalies(days)
        fraud_patterns = service.detect_pattern_fraud(days)
        
        # Calculate overall risk score
        risk_score = len(sales_anomalies) * 2 + len(inventory_anomalies) * 3 + len(fraud_patterns) * 5
        
        return response.Response({
            'risk_score': min(risk_score, 100),
            'sales_anomalies': sales_anomalies,
            'inventory_anomalies': inventory_anomalies,
            'fraud_patterns': fraud_patterns,
            'timestamp': timezone.now().isoformat()
        })

class FraudMetricsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        org = get_org(request)
        
        # Get basic metrics
        total_sales = Sale.objects.filter(organization=org).count()
        total_movements = StockMovement.objects.filter(organization=org).count()
        
        # Get recent suspicious activity
        recent_suspicious = Sale.objects.filter(
            organization=org,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return response.Response({
            'total_sales': total_sales,
            'total_stock_movements': total_movements,
            'recent_suspicious_activity': recent_suspicious,
            'alert_level': 'low' if recent_suspicious < 5 else 'medium' if recent_suspicious < 20 else 'high'
        })

class FraudAlertView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        org = get_org(request)
        service = FraudDetectionService(org)
        
        # Get latest alerts
        anomalies = service.detect_sales_anomalies(1)  # Last day only
        
        alerts = []
        for anomaly in anomalies:
            if anomaly['confidence'] > 0.5:  # High confidence anomalies
                alerts.append({
                    'type': 'sales_anomaly',
                    'sale_id': anomaly['sale_id'],
                    'total': anomaly['total'],
                    'date': anomaly['date'],
                    'reason': 'Unusual sales pattern detected'
                })
        
        return response.Response({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': timezone.now().isoformat()
        })