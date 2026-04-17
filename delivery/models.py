from django.db import models


DELIVERY_STATUS_CHOICES = [
    ('planned', 'Запланирован'),
    ('in_progress', 'В пути'),
    ('completed', 'Выполнен'),
    ('cancelled', 'Отменён'),
]

DELIVERY_STATUS_COLOR = {
    'planned': 'secondary',
    'in_progress': 'info',
    'completed': 'success',
    'cancelled': 'dark',
}

DELIVERY_DIRECTION_CHOICES = [
    ('delivery', 'Отгрузка (к клиенту)'),
    ('return', 'Возврат (от клиента)'),
]


class Driver(models.Model):
    full_name = models.CharField('ФИО', max_length=200)
    phone = models.CharField('Телефон', max_length=50, blank=True)
    license_number = models.CharField('Номер ВУ', max_length=50, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Водитель'
        verbose_name_plural = 'Водители'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Vehicle(models.Model):
    name = models.CharField('Название / марка', max_length=200)
    reg_number = models.CharField('Гос. номер', max_length=30, unique=True)
    capacity_tons = models.DecimalField(
        'Грузоподъёмность (т)', max_digits=6, decimal_places=2, default=0
    )
    volume_m3 = models.DecimalField(
        'Объём кузова (м³)', max_digits=6, decimal_places=2, default=0,
        help_text='Оставьте 0 если неизвестно'
    )
    is_active = models.BooleanField('Активна', default=True)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Транспортное средство'
        verbose_name_plural = 'Транспортные средства'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.reg_number})'


class Delivery(models.Model):
    deal = models.ForeignKey(
        'deals.Deal', on_delete=models.PROTECT,
        related_name='deliveries', verbose_name='Сделка'
    )
    direction = models.CharField(
        'Направление', max_length=20,
        choices=DELIVERY_DIRECTION_CHOICES, default='delivery'
    )
    driver = models.ForeignKey(
        Driver, on_delete=models.PROTECT,
        related_name='deliveries', verbose_name='Водитель',
        null=True, blank=True
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.PROTECT,
        related_name='deliveries', verbose_name='Транспортное средство',
        null=True, blank=True
    )

    planned_date = models.DateField('Плановая дата')
    planned_time = models.TimeField('Плановое время', null=True, blank=True)
    actual_date = models.DateField('Фактическая дата', null=True, blank=True)

    address = models.TextField(
        'Адрес', blank=True,
        help_text='По умолчанию берётся адрес из сделки'
    )
    status = models.CharField(
        'Статус', max_length=20,
        choices=DELIVERY_STATUS_CHOICES, default='planned'
    )

    cost = models.DecimalField(
        'Стоимость рейса (₽)', max_digits=10, decimal_places=2, default=0
    )
    notes = models.TextField('Примечания', blank=True)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Рейс'
        verbose_name_plural = 'Рейсы'
        ordering = ['-planned_date', '-created_at']

    def __str__(self):
        return (
            f'{self.get_direction_display()} — сделка №{self.deal.number} '
            f'({self.planned_date})'
        )

    @property
    def status_color(self):
        return DELIVERY_STATUS_COLOR.get(self.status, 'secondary')

    @property
    def status_label(self):
        return dict(DELIVERY_STATUS_CHOICES).get(self.status, self.status)

    @property
    def effective_address(self):
        return self.address or self.deal.delivery_address or '—'
