from django.db import models
from tenants.models import Organization
from catalog.models import Product
from inventory.models import Workspace

class BillOfMaterials(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bom_as_product')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.product.name} - v{self.version}"

class BomItem(models.Model):
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    component = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='used_in_boms')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='pcs')
    waste_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ('bom', 'component')
    
    def __str__(self):
        return f"{self.quantity} x {self.component.name}"

class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('quality_check', 'Quality Check'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    completed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO-{self.id} - {self.product.name}"

class ProductionStep(models.Model):
    STEP_TYPES = [
        ('preparation', 'Preparation'),
        ('assembly', 'Assembly'),
        ('quality', 'Quality Control'),
        ('packaging', 'Packaging'),
    ]
    
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(max_length=20, choices=STEP_TYPES)
    order = models.IntegerField()
    description = models.TextField()
    estimated_duration_minutes = models.IntegerField()
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.production_order.id} - Step {self.order}"

class QualityCheck(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('rework', 'Rework Required'),
    ]
    
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='quality_checks')
    checked_by = models.ForeignKey('hr.Employee', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    quantity_checked = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_passed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_failed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    defects = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)