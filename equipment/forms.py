from django import forms
from .models import EquipmentType


class EquipmentTypeForm(forms.ModelForm):
    class Meta:
        model = EquipmentType
        fields = [
            'code', 'name', 'category',
            'unit', 'base_price', 'price_coefficient',
            'daily_rental_rate',
            'weight_per_unit', 'volume_per_unit',
            'is_active',
        ]
        labels = {
            'code': 'Код (латиница, уникальный)',
            'name': 'Наименование',
            'category': 'Категория',
            'unit': 'Единица измерения',
            'base_price': 'Базовая цена (Абрис), ₽',
            'price_coefficient': 'Коэффициент цены',
            'daily_rental_rate': 'Суточная ставка аренды, ₽',
            'weight_per_unit': 'Вес единицы, кг',
            'volume_per_unit': 'Объём единицы, м³',
            'is_active': 'Активно',
        }
        help_texts = {
            'price_coefficient': 'Наша цена = база × коэффициент (округление до 10 ₽). По умолчанию 1.15 для лесов.',
            'daily_rental_rate': 'Базовая суточная ставка для ручного ввода; калькулятор пересчитывает её автоматически.',
        }
        widgets = {
            'code': forms.TextInput(attrs={'placeholder': 'например: frame_std'}),
        }
