from django.db import models
import math


class EquipmentType(models.Model):
    code = models.CharField('Код', max_length=50, unique=True)
    name = models.CharField('Наименование', max_length=200)
    category = models.ForeignKey(
        'pricing.EquipmentCategory', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='equipment_types',
        verbose_name='Категория',
    )
    unit = models.CharField('Ед. изм.', max_length=20, default='шт')
    base_price = models.DecimalField(
        'Рыночная стоимость ед.', max_digits=10, decimal_places=2, default=0,
    )
    price_coefficient = models.DecimalField(
        'Коэффициент цены', max_digits=5, decimal_places=2, default=1.0,
    )
    daily_rental_rate = models.DecimalField(
        'Суточная ставка аренды (руб.)', max_digits=10, decimal_places=2, default=0,
    )
    weight_per_unit = models.DecimalField('Вес ед. (кг)', max_digits=8, decimal_places=3, default=0)
    volume_per_unit = models.DecimalField('Объём ед. (м3)', max_digits=8, decimal_places=4, default=0)
    is_active = models.BooleanField('Активно', default=True)

    class Meta:
        verbose_name = 'Тип оборудования'
        verbose_name_plural = 'Типы оборудования'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def unit_price(self):
        price = float(self.base_price) * float(self.price_coefficient)
        return int(math.ceil(price / 10) * 10)


class WarehouseStock(models.Model):
    equipment_type = models.OneToOneField(EquipmentType, on_delete=models.CASCADE,
                                          related_name='stock', verbose_name='Тип оборудования')
    quantity_total = models.IntegerField('Всего', default=0)
    quantity_reserved = models.IntegerField('Зарезервировано', default=0)
    quantity_rented = models.IntegerField('В аренде', default=0)
    quantity_repair = models.IntegerField('На ремонте', default=0)
    min_stock_level = models.IntegerField('Мин. запас', default=0)

    class Meta:
        verbose_name = 'Остаток на складе'
        verbose_name_plural = 'Остатки на складе'

    def __str__(self):
        return f'{self.equipment_type.name}: {self.quantity_available} шт. доступно'

    @property
    def quantity_available(self):
        return max(0, self.quantity_total - self.quantity_reserved - self.quantity_rented - self.quantity_repair)

    @property
    def is_low_stock(self):
        return self.quantity_available <= self.min_stock_level


class EquipmentMovement(models.Model):
    MOVEMENT_TYPES = [
        ('in', 'Поступление'),
        ('out_reserve', 'Резервирование'),
        ('out_rent', 'Выдача в аренду'),
        ('return', 'Возврат с аренды'),
        ('cancel_reserve', 'Снятие резерва'),
        ('repair_out', 'Отправка на ремонт'),
        ('repair_in', 'Возврат с ремонта'),
        ('writeoff', 'Списание'),
        ('adjustment', 'Корректировка'),
    ]

    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.CASCADE,
                                       related_name='movements', verbose_name='Тип оборудования')
    movement_type = models.CharField('Тип движения', max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField('Количество')
    deal = models.ForeignKey('deals.Deal', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='movements', verbose_name='Сделка')
    date = models.DateTimeField('Дата', auto_now_add=True)
    notes = models.TextField('Примечания', blank=True)
    created_by = models.CharField('Создал', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Движение оборудования'
        verbose_name_plural = 'Движения оборудования'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_movement_type_display()} — {self.equipment_type.name} x{self.quantity}'
