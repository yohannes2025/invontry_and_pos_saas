from rest_framework import serializers
from .models import BillOfMaterials, BomItem, ProductionOrder, ProductionStep, QualityCheck

class BomItemSerializer(serializers.ModelSerializer):
    component_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BomItem
        fields = '__all__'
    
    def get_component_name(self, obj):
        return obj.component.name

class BillOfMaterialsSerializer(serializers.ModelSerializer):
    items = BomItemSerializer(many=True, read_only=True)
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BillOfMaterials
        fields = '__all__'
        read_only_fields = ('organization',)
    
    def get_product_name(self, obj):
        return obj.product.name

class ProductionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionStep
        fields = '__all__'

class QualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = '__all__'

class ProductionOrderSerializer(serializers.ModelSerializer):
    steps = ProductionStepSerializer(many=True, read_only=True)
    quality_checks = QualityCheckSerializer(many=True, read_only=True)
    product_name = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductionOrder
        fields = '__all__'
        read_only_fields = ('organization',)
    
    def get_product_name(self, obj):
        return obj.product.name
    
    def get_progress(self, obj):
        if obj.quantity > 0:
            return float(obj.completed_quantity / obj.quantity) * 100
        return 0

class BomCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    name = serializers.CharField()
    items = serializers.ListField(
        child=serializers.DictField()
    )