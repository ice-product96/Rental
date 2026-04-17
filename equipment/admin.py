from django.contrib import admin
from .models import EquipmentType, WarehouseStock, EquipmentMovement


class WarehouseStockInline(admin.StackedInline):
    model = WarehouseStock
    extra = 1


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'base_price', 'price_coefficient', 'unit_price_display', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']
    inlines = [WarehouseStockInline]

    def unit_price_display(self, obj):
        return f'{obj.unit_price} ₽'
    unit_price_display.short_description = 'Наша цена'


@admin.register(WarehouseStock)
class WarehouseStockAdmin(admin.ModelAdmin):
    list_display = ['equipment_type', 'quantity_total', 'quantity_available_display',
                    'quantity_reserved', 'quantity_rented', 'quantity_repair']
    readonly_fields = ['quantity_available_display']

    def quantity_available_display(self, obj):
        return obj.quantity_available
    quantity_available_display.short_description = 'Доступно'


@admin.register(EquipmentMovement)
class EquipmentMovementAdmin(admin.ModelAdmin):
    list_display = ['date', 'equipment_type', 'movement_type', 'quantity', 'deal']
    list_filter = ['movement_type', 'equipment_type']
    readonly_fields = ['date']
    autocomplete_fields = ['deal']
