from django.contrib import admin
from .models import Driver, Vehicle, Delivery


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'license_number', 'is_active']
    list_filter = ['is_active']
    search_fields = ['full_name', 'phone', 'license_number']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['name', 'reg_number', 'capacity_tons', 'volume_m3', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'reg_number']


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'deal', 'direction', 'driver', 'vehicle', 'planned_date', 'status']
    list_filter = ['status', 'direction']
    search_fields = ['deal__number', 'deal__client__name', 'driver__full_name', 'vehicle__reg_number']
    raw_id_fields = ['deal']
    date_hierarchy = 'planned_date'
