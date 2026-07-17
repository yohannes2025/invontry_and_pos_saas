from django.urls import path
from .views import FraudDetectionView, FraudMetricsView, FraudAlertView

urlpatterns = [
    path('detect/', FraudDetectionView.as_view(), name='fraud_detect'),
    path('metrics/', FraudMetricsView.as_view(), name='fraud_metrics'),
    path('alerts/', FraudAlertView.as_view(), name='fraud_alerts'),
]