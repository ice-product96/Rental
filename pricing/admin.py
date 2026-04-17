from django.contrib import admin
from django import forms

from .models import EquipmentCategory, PricingCoefficientSettings


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'algorithm_code', 'deposit_pct_default', 'use_city_coeff', 'is_active', 'ordering')
    list_editable = ('ordering', 'is_active')
    list_filter = ('algorithm_code', 'is_active')


class PricingCoefficientSettingsAdminForm(forms.ModelForm):
    city_coefficients = forms.JSONField(
        required=False,
        help_text='JSON-словарь формата {"Екатеринбург": 1.0, "Пермь": 1.15}',
        widget=forms.Textarea(attrs={'rows': 6, 'style': 'font-family:monospace;'}),
    )

    class Meta:
        model = PricingCoefficientSettings
        fields = '__all__'


@admin.register(PricingCoefficientSettings)
class PricingCoefficientSettingsAdmin(admin.ModelAdmin):
    form = PricingCoefficientSettingsAdminForm
    fieldsets = (
        ('Леса', {
            'fields': ('scaffold_season_coeff_default', 'scaffold_price_coeff_default'),
        }),
        ('Вышки-туры', {
            'fields': ('tower_psrv21_model_coeff', 'tower_psrv22_model_coeff', 'tower_psrv22_extra_charge'),
        }),
        ('Города', {
            'fields': ('city_coefficients',),
        }),
        ('Служебное', {
            'fields': ('updated_at',),
        }),
    )
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        if PricingCoefficientSettings.objects.exists():
            return False
        return super().has_add_permission(request)
