from django import forms
from .models import Delivery, Driver, Vehicle


class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = [
            'direction', 'driver', 'vehicle',
            'planned_date', 'planned_time', 'actual_date',
            'address', 'cost', 'notes',
        ]
        widgets = {
            'planned_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_time': forms.TimeInput(attrs={'type': 'time'}),
            'actual_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, deal=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только активных водителей и машины
        self.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(is_active=True)
        # Подсказка: адрес из сделки
        if deal and deal.delivery_address and not self.instance.pk:
            self.fields['address'].initial = deal.delivery_address
        self.fields['driver'].empty_label = '— не назначен —'
        self.fields['vehicle'].empty_label = '— не назначена —'


class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['full_name', 'phone', 'license_number', 'is_active', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['name', 'reg_number', 'capacity_tons', 'volume_m3', 'is_active', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
