import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from pos.models import Sale, SaleItem
from inventory.models import StockMovement

class FraudDetectionService:
    def __init__(self, organization):
        self.organization = organization
    
    def detect_sales_anomalies(self, days=30):
        """Detect anomalous sales using Isolation Forest"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get sales data
        sales = Sale.objects.filter(
            organization=self.organization,
            created_at__range=[start_date, end_date]
        ).values('created_at', 'total', 'id')
        
        if not sales:
            return []
        
        # Prepare features for anomaly detection
        data = []
        sale_ids = []
        
        for sale in sales:
            # Calculate features
            hour = sale['created_at'].hour
            day_of_week = sale['created_at'].weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            data.append([
                float(sale['total']),
                hour,
                day_of_week,
                is_weekend
            ])
            sale_ids.append(sale['id'])
        
        # Normalize data
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data)
        
        # Train Isolation Forest
        model = IsolationForest(contamination=0.1, random_state=42)
        predictions = model.fit_predict(data_scaled)
        
        # Identify anomalies (-1 indicates anomaly)
        anomalies = []
        for i, pred in enumerate(predictions):
            if pred == -1:
                anomalies.append({
                    'sale_id': sale_ids[i],
                    'total': float(sales[i]['total']),
                    'date': sales[i]['created_at'].isoformat(),
                    'confidence': float(model.score_samples([data_scaled[i]])[0])
                })
        
        return anomalies
    
    def detect_inventory_anomalies(self, days=30):
        """Detect suspicious inventory movements"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        movements = StockMovement.objects.filter(
            organization=self.organization,
            created_at__range=[start_date, end_date]
        ).values('product', 'type', 'quantity', 'created_at')
        
        if not movements:
            return []
        
        # Group by product
        product_movements = {}
        for movement in movements:
            product_id = movement['product']
            if product_id not in product_movements:
                product_movements[product_id] = []
            product_movements[product_id].append({
                'type': movement['type'],
                'quantity': float(movement['quantity']),
                'date': movement['created_at']
            })
        
        anomalies = []
        for product_id, movs in product_movements.items():
            # Check for unusual patterns
            quantities = [m['quantity'] for m in movs]
            if quantities:
                mean_qty = np.mean(quantities)
                std_qty = np.std(quantities)
                
                for mov in movs:
                    # Flag if quantity is more than 3 standard deviations from mean
                    if std_qty > 0 and abs(mov['quantity'] - mean_qty) > 3 * std_qty:
                        anomalies.append({
                            'product_id': product_id,
                            'type': mov['type'],
                            'quantity': mov['quantity'],
                            'date': mov['date'].isoformat(),
                            'reason': 'Unusual quantity (3+ std dev)'
                        })
        
        return anomalies
    
    def detect_pattern_fraud(self, days=7):
        """Detect common fraud patterns"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        patterns = []
        
        # Pattern 1: Repeated sales of same item in short period
        sales = Sale.objects.filter(
            organization=self.organization,
            created_at__range=[start_date, end_date]
        ).prefetch_related('items')
        
        item_counts = {}
        for sale in sales:
            for item in sale.items.all():
                key = f"{sale.created_at.date()}_{item.product_id}"
                item_counts[key] = item_counts.get(key, 0) + int(item.quantity)
        
        for key, count in item_counts.items():
            if count > 100:  # Threshold for suspicion
                patterns.append({
                    'pattern': 'High volume same item in single day',
                    'date': key.split('_')[0],
                    'product_id': int(key.split('_')[1]),
                    'quantity': count,
                    'severity': 'high'
                })
        
        # Pattern 2: Sales at unusual hours
        late_night_sales = Sale.objects.filter(
            organization=self.organization,
            created_at__hour__gte=23,
            created_at__hour__lte=5
        ).count()
        
        if late_night_sales > 10:  # Threshold
            patterns.append({
                'pattern': 'High number of late night sales',
                'count': late_night_sales,
                'period': f'{start_date.date()} to {end_date.date()}',
                'severity': 'medium'
            })
        
        return patterns