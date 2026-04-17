from django.contrib import admin
from .models import Deal, DealSection, DealEquipmentItem, PartialReturn, PartialReturnItem, DealStatusHistory


class DealSectionInline(admin.TabularInline):
    model = DealSection
    extra = 0
    show_change_link = True


class DealEquipmentItemInline(admin.TabularInline):
    model = DealEquipmentItem
    extra = 0


class DealStatusHistoryInline(admin.TabularInline):
    model = DealStatusHistory
    extra = 0
    readonly_fields = ['changed_at']


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['number', 'client', 'category_names', 'status', 'rental_days', 'grand_total', 'created_at']
    list_filter = ['status', 'city']
    search_fields = ['number', 'client__name']
    readonly_fields = ['number', 'created_at', 'updated_at']
    inlines = [DealSectionInline, DealEquipmentItemInline, DealStatusHistoryInline]


@admin.register(DealSection)
class DealSectionAdmin(admin.ModelAdmin):
    list_display = ['deal', 'category', 'ordering', 'daily_cost', 'total_rental']
