from django.db import models
from .defaults import (
    DEFAULT_CITY_COEFFICIENTS,
    DEFAULT_SCAFFOLD_SEASON_COEFF,
    DEFAULT_SCAFFOLD_PRICE_COEFF,
    DEFAULT_TOWER_MODEL_COEFFS,
    DEFAULT_TOWER_PSRV22_EXTRA_CHARGE,
)

ALGORITHM_CHOICES = [
    ('area_based', 'По площади (строительные леса)'),
    ('tower', 'Вышки-туры'),
    ('daily_rate', 'Посуточная (любая техника)'),
]


class EquipmentCategory(models.Model):
    name = models.CharField('Название', max_length=100)
    algorithm_code = models.CharField(
        'Алгоритм расчёта', max_length=50,
        choices=ALGORITHM_CHOICES, default='daily_rate',
    )
    deposit_pct_default = models.DecimalField(
        'Залог % (по умолч.)', max_digits=5, decimal_places=2, default=10,
    )
    use_city_coeff = models.BooleanField('Применять городской коэф.', default=True)
    is_active = models.BooleanField('Активна', default=True)
    ordering = models.IntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория техники'
        verbose_name_plural = 'Категории техники'
        ordering = ['ordering', 'name']

    def __str__(self):
        return self.name

    def get_algorithm(self):
        from .algorithms import get_algorithm
        return get_algorithm(self.algorithm_code)


class PricingCoefficientSettings(models.Model):
    city_coefficients = models.JSONField('Коэффициенты городов', default=dict, blank=True)
    scaffold_season_coeff_default = models.DecimalField(
        'Сезонный коэф. (леса) по умолчанию',
        max_digits=6,
        decimal_places=3,
        default=DEFAULT_SCAFFOLD_SEASON_COEFF,
    )
    scaffold_price_coeff_default = models.DecimalField(
        'Коэф. цен (леса) по умолчанию',
        max_digits=6,
        decimal_places=3,
        default=DEFAULT_SCAFFOLD_PRICE_COEFF,
    )
    tower_psrv21_model_coeff = models.DecimalField(
        'Коэф. модели ПСРВ-21',
        max_digits=6,
        decimal_places=3,
        default=DEFAULT_TOWER_MODEL_COEFFS['ПСРВ-21'],
    )
    tower_psrv22_model_coeff = models.DecimalField(
        'Коэф. модели ПСРВ-22',
        max_digits=6,
        decimal_places=3,
        default=DEFAULT_TOWER_MODEL_COEFFS['ПСРВ-22'],
    )
    tower_psrv22_extra_charge = models.DecimalField(
        'Доп. наценка ПСРВ-22 (руб.)',
        max_digits=8,
        decimal_places=2,
        default=DEFAULT_TOWER_PSRV22_EXTRA_CHARGE,
    )
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Настройки коэффициентов'
        verbose_name_plural = 'Настройки коэффициентов'

    def __str__(self):
        return 'Настройки коэффициентов'

    @classmethod
    def get_solo(cls):
        defaults = {
            'city_coefficients': dict(DEFAULT_CITY_COEFFICIENTS),
            'scaffold_season_coeff_default': DEFAULT_SCAFFOLD_SEASON_COEFF,
            'scaffold_price_coeff_default': DEFAULT_SCAFFOLD_PRICE_COEFF,
            'tower_psrv21_model_coeff': DEFAULT_TOWER_MODEL_COEFFS['ПСРВ-21'],
            'tower_psrv22_model_coeff': DEFAULT_TOWER_MODEL_COEFFS['ПСРВ-22'],
            'tower_psrv22_extra_charge': DEFAULT_TOWER_PSRV22_EXTRA_CHARGE,
        }
        obj, _ = cls.objects.get_or_create(pk=1, defaults=defaults)
        if not obj.city_coefficients:
            obj.city_coefficients = dict(DEFAULT_CITY_COEFFICIENTS)
            obj.save(update_fields=['city_coefficients', 'updated_at'])
        return obj
