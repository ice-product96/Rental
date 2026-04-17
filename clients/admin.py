from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_type', 'phone', 'city', 'inn', 'created_at']
    list_filter = ['client_type', 'city']
    search_fields = ['name', 'phone', 'inn', 'email']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Основное', {'fields': ('client_type', 'name', 'phone', 'email', 'city', 'address', 'notes')}),
        ('Физическое лицо', {'fields': ('passport_series', 'passport_number', 'passport_issued_by',
                                         'passport_issued_date', 'birth_date', 'registration_address'),
                              'classes': ('collapse',)}),
        ('Юридическое лицо', {'fields': ('company_full_name', 'inn', 'kpp', 'ogrn', 'director',
                                          'director_short', 'director_title', 'legal_address',
                                          'bank_name', 'bank_account', 'bank_bik', 'bank_corr_account'),
                               'classes': ('collapse',)}),
        ('Служебное', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
