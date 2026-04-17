from django.contrib import admin
from .models import EquipmentCategory


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'algorithm_code', 'deposit_pct_default', 'use_city_coeff', 'is_active', 'ordering')
    list_editable = ('ordering', 'is_active')
    list_filter = ('algorithm_code', 'is_active')
