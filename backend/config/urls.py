from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/tenants/', include('tenants.urls')),
    path('api/catalog/', include('catalog.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/pos/', include('pos.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/ai/', include('ai.urls')),
    path('api/erp/', include('erp.urls')),  # Add ERP URLs
    path('api/billing/', include('billing.urls')),
    path('api/logistics/', include('logistics.urls')),  # Add logistics URLs
    path('api/hr/', include('hr.urls')),  # Add HR URLs
    path('api/manufacturing/', include('manufacturing.urls')),  # Add manufacturing URLs
    path('api/fraud/', include('fraud_detection.urls')),  # Add fraud detection URLs
]