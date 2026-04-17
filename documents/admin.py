from django.contrib import admin
from .models import OurLegalEntity, ContractTemplate, GeneratedContract


@admin.register(OurLegalEntity)
class OurLegalEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'entity_type', 'inn', 'is_default', 'updated_at')
    list_filter = ('entity_type', 'is_default')


@admin.register(ContractTemplate)
class ContractTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'document_type', 'slug', 'is_active', 'updated_at')
    list_filter = ('document_type', 'is_active',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(GeneratedContract)
class GeneratedContractAdmin(admin.ModelAdmin):
    list_display = ('number', 'contract_date', 'client', 'template', 'created_at')
    list_filter = ('contract_date', 'template')
    raw_id_fields = ('client', 'deal', 'our_entity', 'template')
    readonly_fields = ('rendered_html', 'created_at', 'updated_at')
