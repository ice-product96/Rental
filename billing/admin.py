from django.contrib import admin
from .models import Invoice, InvoiceItem, ShippingDocument, ShippingDocumentItem, NonReturnAct, NonReturnActItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class ShippingDocItemInline(admin.TabularInline):
    model = ShippingDocumentItem
    extra = 0


class NonReturnItemInline(admin.TabularInline):
    model = NonReturnActItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'deal', 'invoice_type', 'date', 'total', 'status']
    list_filter = ['status', 'invoice_type']
    search_fields = ['number', 'deal__number', 'deal__client__name']
    readonly_fields = ['created_at']
    inlines = [InvoiceItemInline]


@admin.register(ShippingDocument)
class ShippingDocAdmin(admin.ModelAdmin):
    list_display = ['number', 'deal', 'doc_type', 'date']
    inlines = [ShippingDocItemInline]


@admin.register(NonReturnAct)
class NonReturnActAdmin(admin.ModelAdmin):
    list_display = ['number', 'deal', 'date', 'total_amount']
    inlines = [NonReturnItemInline]
