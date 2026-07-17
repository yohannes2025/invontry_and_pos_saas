from rest_framework import viewsets, generics, permissions, response, status
from rest_framework.decorators import action
from django.utils import timezone
from django.db import transaction
from .models import BillOfMaterials, BomItem, ProductionOrder, ProductionStep, QualityCheck
from .serializers import BillOfMaterialsSerializer, ProductionOrderSerializer, QualityCheckSerializer
from catalog.models import Product
from inventory.models import StockLevel, StockMovement
from tenants.models import Organization

def get_org(request):
    org_slug = request.headers.get('X-Org-Slug')
    return Organization.objects.get(slug=org_slug)

class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return BillOfMaterials.objects.filter(organization=org, is_active=True)
    
    def perform_create(self, serializer):
        org = get_org(self.request)
        serializer.save(organization=org)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        bom = self.get_object()
        component_id = request.data.get('component_id')
        quantity = request.data.get('quantity')
        
        if not component_id or not quantity:
            return response.Response(
                {'error': 'component_id and quantity required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        component = Product.objects.get(id=component_id, organization=bom.organization)
        bom_item = BomItem.objects.create(
            bom=bom,
            component=component,
            quantity=quantity,
            unit=request.data.get('unit', 'pcs'),
            waste_percentage=request.data.get('waste_percentage', 0)
        )
        
        return response.Response(BomItemSerializer(bom_item).data)

class ProductionOrderViewSet(viewsets.ModelViewSet):
    serializer_class = ProductionOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        org = get_org(self.request)
        return ProductionOrder.objects.filter(organization=org)
    
    def perform_create(self, serializer):
        org = get_org(self.request)
        product_id = self.request.data.get('product')
        product = Product.objects.get(id=product_id, organization=org)
        bom = BillOfMaterials.objects.get(id=self.request.data.get('bom'), organization=org)
        
        serializer.save(organization=org, product=product, bom=bom)
        
        # Create production steps
        steps = [
            ('preparation', 'Prepare materials and workspace', 30),
            ('assembly', 'Assemble product components', 60),
            ('quality', 'Quality control inspection', 20),
            ('packaging', 'Package finished products', 15),
        ]
        
        for i, (step_type, desc, duration) in enumerate(steps, 1):
            ProductionStep.objects.create(
                production_order=serializer.instance,
                step_type=step_type,
                order=i,
                description=desc,
                estimated_duration_minutes=duration
            )
    
    @action(detail=True, methods=['post'])
    def start_production(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'planned':
            return response.Response(
                {'error': 'Order must be planned to start'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check stock availability for components
        bom = order.bom
        missing_components = []
        
        for item in bom.items.all():
            stock = StockLevel.objects.filter(
                workspace=order.workspace,
                product=item.component
            ).first()
            
            required = item.quantity * order.quantity * (1 + item.waste_percentage / 100)
            available = stock.quantity if stock else 0
            
            if available < required:
                missing_components.append({
                    'product': item.component.name,
                    'required': float(required),
                    'available': float(available)
                })
        
        if missing_components:
            return response.Response(
                {'error': 'Insufficient stock', 'missing': missing_components},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Deduct components from stock
        for item in bom.items.all():
            stock = StockLevel.objects.get(
                workspace=order.workspace,
                product=item.component
            )
            required = item.quantity * order.quantity * (1 + item.waste_percentage / 100)
            stock.quantity -= required
            stock.save()
            
            StockMovement.objects.create(
                organization=order.organization,
                workspace_from=order.workspace,
                workspace_to=None,
                product=item.component,
                quantity=required,
                type='out',
                created_by=request.user
            )
        
        order.status = 'in_progress'
        order.actual_start = timezone.now()
        order.save()
        
        return response.Response(ProductionOrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def complete_production(self, request, pk=None):
        order = self.get_object()
        
        if order.status != 'in_progress':
            return response.Response(
                {'error': 'Order must be in progress to complete'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add finished product to stock
        stock, created = StockLevel.objects.get_or_create(
            organization=order.organization,
            workspace=order.workspace,
            product=order.product,
            defaults={'quantity': 0}
        )
        stock.quantity += order.quantity
        stock.save()
        
        StockMovement.objects.create(
            organization=order.organization,
            workspace_from=None,
            workspace_to=order.workspace,
            product=order.product,
            quantity=order.quantity,
            type='in',
            created_by=request.user
        )
        
        order.completed_quantity = order.quantity
        order.status = 'completed'
        order.actual_end = timezone.now()
        order.save()
        
        return response.Response(ProductionOrderSerializer(order).data)
    
    @action(detail=True, methods=['post'])
    def quality_check(self, request, pk=None):
        order = self.get_object()
        checked_by_id = request.data.get('checked_by')
        quantity_checked = request.data.get('quantity_checked')
        status_val = request.data.get('status')
        
        if not checked_by_id or not quantity_checked or not status_val:
            return response.Response(
                {'error': 'checked_by, quantity_checked, and status required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        quality_check = QualityCheck.objects.create(
            production_order=order,
            checked_by_id=checked_by_id,
            quantity_checked=quantity_checked,
            status=status_val,
            defects=request.data.get('defects', ''),
            notes=request.data.get('notes', '')
        )
        
        if status_val == 'passed':
            order.status = 'quality_check'
            order.save()
        elif status_val == 'failed':
            order.status = 'cancelled'
            order.save()
        
        return response.Response(QualityCheckSerializer(quality_check).data)