from django.db import models

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
