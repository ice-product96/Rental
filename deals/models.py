from django.db import models
from django.utils import timezone


DEAL_STATUS_CHOICES = [
    ('new', 'Новая заявка'),
    ('calculation', 'Расчёт'),
    ('confirmed', 'Подтверждена'),
    ('contract_signed', 'Договор подписан'),
    ('invoice_sent', 'Счёт выставлен'),
    ('paid', 'Оплачено'),
    ('delivery', 'Отгрузка'),
    ('rented', 'В аренде'),
    ('partial_return', 'Частичный возврат'),
    ('returned', 'Возвращено'),
    ('overdue', 'Просрочено'),
    ('cancelled', 'Отменена'),
    ('non_return', 'Акт невозврата'),
]

STATUS_COLOR = {
    'new': 'secondary',
    'calculation': 'info',
    'confirmed': 'primary',
    'contract_signed': 'primary',
    'invoice_sent': 'warning',
    'paid': 'success',
    'delivery': 'info',
    'rented': 'success',
    'partial_return': 'warning',
    'returned': 'secondary',
    'overdue': 'danger',
    'cancelled': 'dark',
    'non_return': 'danger',
}

CITY_CHOICES = [
    ('Екатеринбург', 'Екатеринбург'),
    ('Пермь', 'Пермь'),
    ('Новосибирск', 'Новосибирск'),
    ('Челябинск', 'Челябинск'),
]

VAT_CHOICES = [
    ('no_vat', 'Без НДС'),
    ('with_vat', 'С НДС (20%)'),
]


class Deal(models.Model):
    """
    A deal may contain multiple sections — each section has its own equipment
    category and pricing algorithm. Financials are aggregated across all sections.
    """
    number = models.CharField('Номер сделки', max_length=50, unique=True)
    client = models.ForeignKey('clients.Client', on_delete=models.PROTECT,
                               related_name='deals', verbose_name='Клиент')
    our_entity = models.ForeignKey(
        'documents.OurLegalEntity',
        on_delete=models.PROTECT,
        related_name='deals',
        verbose_name='Наша организация',
        null=True,
        blank=True,
    )
    status = models.CharField('Статус', max_length=30, choices=DEAL_STATUS_CHOICES, default='new')

    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    start_date = models.DateField('Дата начала аренды', null=True, blank=True)
    end_date = models.DateField('Дата окончания аренды', null=True, blank=True)
    actual_return_date = models.DateField('Фактический возврат', null=True, blank=True)

    city = models.CharField('Город', max_length=50, choices=CITY_CHOICES, default='Екатеринбург')
    delivery_address = models.TextField('Адрес доставки', blank=True)
    delivery_cost = models.DecimalField('Стоимость доставки (1 рейс)', max_digits=10, decimal_places=2, default=0)

    vat_mode = models.CharField('НДС', max_length=20, choices=VAT_CHOICES, default='no_vat')
    deposit_pct = models.DecimalField('Залог %', max_digits=5, decimal_places=2, default=10)

    # Aggregated financials (sum of all sections + deal-level delivery/VAT)
    total_area = models.DecimalField('Площадь (м²)', max_digits=10, decimal_places=2, default=0)
    rental_days = models.IntegerField('Срок аренды (дней)', default=30)
    daily_cost = models.DecimalField('Суточная стоимость', max_digits=10, decimal_places=2, default=0)
    total_rental = models.DecimalField('Итого аренда', max_digits=12, decimal_places=2, default=0)
    market_value = models.DecimalField('Рыночная стоимость оборудования', max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField('Сумма залога', max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField('Итого к оплате', max_digits=12, decimal_places=2, default=0)

    notes = models.TextField('Примечания', blank=True)
    contract_number = models.CharField('Номер договора', max_length=100, blank=True)
    contract_date = models.DateField('Дата договора', null=True, blank=True)

    class Meta:
        verbose_name = 'Сделка'
        verbose_name_plural = 'Сделки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Сделка №{self.number} — {self.client.name}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from datetime import date
        today = date.today()
        prefix = today.strftime('%Y%m')
        last = Deal.objects.filter(number__startswith=prefix).order_by('-number').first()
        if last:
            try:
                seq = int(last.number[-3:]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f'{prefix}{seq:03d}'

    @property
    def status_color(self):
        return STATUS_COLOR.get(self.status, 'secondary')

    @property
    def status_label(self):
        return dict(DEAL_STATUS_CHOICES).get(self.status, self.status)

    @property
    def days_remaining(self):
        if self.end_date:
            today = timezone.now().date()
            return (self.end_date - today).days
        return None

    @property
    def days_overdue(self):
        r = self.days_remaining
        return abs(r) if r is not None and r < 0 else None

    @property
    def is_overdue(self):
        r = self.days_remaining
        return r is not None and r < 0 and self.status in ('rented', 'partial_return')

    @property
    def category_names(self):
        """Comma-separated list of all section category names."""
        names = list(self.sections.values_list('category__name', flat=True))
        return ', '.join(names) if names else '—'


class DealSection(models.Model):
    """
    One section inside a deal. Each section has its own equipment category
    and pricing algorithm. A deal can have N sections of different types.
    """
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE,
                             related_name='sections', verbose_name='Сделка')
    category = models.ForeignKey('pricing.EquipmentCategory', on_delete=models.PROTECT,
                                 verbose_name='Категория техники')
    ordering = models.IntegerField('Порядок', default=0)
    pricing_params = models.JSONField('Параметры расчёта', default=dict)

    # Section-level calculated financials
    total_area = models.DecimalField('Площадь (м²)', max_digits=10, decimal_places=2, default=0)
    daily_cost = models.DecimalField('Суточная стоимость', max_digits=10, decimal_places=2, default=0)
    total_rental = models.DecimalField('Итого аренда', max_digits=12, decimal_places=2, default=0)
    market_value = models.DecimalField('Рыночная стоимость', max_digits=12, decimal_places=2, default=0)
    deposit_amount = models.DecimalField('Сумма залога', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Раздел сделки'
        verbose_name_plural = 'Разделы сделки'
        ordering = ['ordering']

    def __str__(self):
        return f'{self.category.name} (сделка №{self.deal.number})'


class DealEquipmentItem(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE,
                             related_name='equipment_items', verbose_name='Сделка')
    section = models.ForeignKey(DealSection, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='equipment_items', verbose_name='Раздел')
    equipment_type = models.ForeignKey('equipment.EquipmentType', on_delete=models.PROTECT,
                                       verbose_name='Тип оборудования')
    quantity = models.IntegerField('Количество', default=0)
    unit_price = models.DecimalField('Рыночная цена ед.', max_digits=10, decimal_places=2, default=0)
    daily_rental_rate = models.DecimalField('Суточная ставка (руб./ед.)', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Позиция оборудования'
        verbose_name_plural = 'Позиции оборудования'

    def __str__(self):
        return f'{self.equipment_type.name} x{self.quantity}'

    @property
    def total_value(self):
        return self.quantity * float(self.unit_price)


class PartialReturn(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE,
                             related_name='partial_returns', verbose_name='Сделка')
    return_date = models.DateField('Дата возврата')
    amount_paid = models.DecimalField('Сумма к оплате за период', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Частичный возврат'
        verbose_name_plural = 'Частичные возвраты'
        ordering = ['-return_date']

    def __str__(self):
        return f'Возврат от {self.return_date} по сделке №{self.deal.number}'


class PartialReturnItem(models.Model):
    partial_return = models.ForeignKey(PartialReturn, on_delete=models.CASCADE, related_name='items')
    equipment_type = models.ForeignKey('equipment.EquipmentType', on_delete=models.PROTECT,
                                       verbose_name='Тип оборудования')
    quantity_returned = models.IntegerField('Возвращено, шт')

    class Meta:
        verbose_name = 'Позиция возврата'
        verbose_name_plural = 'Позиции возврата'


class DealStatusHistory(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField('Старый статус', max_length=30, blank=True)
    new_status = models.CharField('Новый статус', max_length=30)
    changed_at = models.DateTimeField('Дата изменения', auto_now_add=True)
    notes = models.TextField('Комментарий', blank=True)

    class Meta:
        verbose_name = 'История статусов'
        verbose_name_plural = 'История статусов'
        ordering = ['-changed_at']
