from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('sent', 'Отправлен'),
        ('paid', 'Оплачен'),
        ('overdue', 'Просрочен'),
        ('cancelled', 'Отменён'),
    ]
    INVOICE_TYPE_CHOICES = [
        ('rental', 'Аренда'),
        ('deposit', 'Залог'),
        ('penalty', 'Штраф/пеня'),
        ('repair', 'Ремонт'),
        ('non_return', 'Невозврат'),
    ]

    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE,
                             related_name='invoices', verbose_name='Сделка')
    number = models.CharField('Номер счёта', max_length=50, unique=True)
    invoice_type = models.CharField('Тип счёта', max_length=20, choices=INVOICE_TYPE_CHOICES, default='rental')
    date = models.DateField('Дата', default=timezone.now)
    due_date = models.DateField('Дата оплаты', null=True, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')

    subtotal = models.DecimalField('Сумма без НДС', max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField('НДС', max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField('Итого', max_digits=12, decimal_places=2, default=0)

    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'Счёт №{self.number} от {self.date}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from datetime import date
        today = date.today()
        prefix = f"СЧ-{today.strftime('%Y%m')}-"
        last = Invoice.objects.filter(number__startswith=prefix).order_by('-number').first()
        seq = 1
        if last:
            try:
                seq = int(last.number.split('-')[-1]) + 1
            except (TypeError, ValueError):
                seq = 1
        candidate = f'{prefix}{seq:03d}'
        while Invoice.objects.filter(number=candidate).exists():
            seq += 1
            candidate = f'{prefix}{seq:03d}'
        return candidate

    @property
    def status_color(self):
        colors = {'draft': 'secondary', 'sent': 'info', 'paid': 'success',
                  'overdue': 'danger', 'cancelled': 'dark'}
        return colors.get(self.status, 'secondary')

    @property
    def is_overdue(self):
        return self.due_date and self.due_date < timezone.now().date() and self.status not in ('paid', 'cancelled')


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name='items', verbose_name='Счёт')
    name = models.CharField('Наименование', max_length=255)
    qty = models.DecimalField('Кол-во', max_digits=10, decimal_places=2, default=1)
    unit = models.CharField('Ед. изм.', max_length=20, default='шт')
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2)
    total = models.DecimalField('Сумма', max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция счёта'
        verbose_name_plural = 'Позиции счёта'

    def __str__(self):
        return f'{self.name} x{self.qty}'


class ShippingDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('issue', 'Акт выдачи (отгрузка)'),
        ('return', 'Акт возврата'),
        ('partial_return', 'Акт частичного возврата'),
    ]

    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE,
                             related_name='shipping_docs', verbose_name='Сделка')
    number = models.CharField('Номер', max_length=50)
    date = models.DateField('Дата')
    doc_type = models.CharField('Тип документа', max_length=20, choices=DOC_TYPE_CHOICES)
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Документ отгрузки'
        verbose_name_plural = 'Документы отгрузки'
        ordering = ['-date']

    def __str__(self):
        return f'{self.get_doc_type_display()} №{self.number} от {self.date}'


class ShippingDocumentItem(models.Model):
    document = models.ForeignKey(ShippingDocument, on_delete=models.CASCADE,
                                 related_name='items', verbose_name='Документ')
    equipment_type = models.ForeignKey('equipment.EquipmentType', on_delete=models.PROTECT,
                                       verbose_name='Тип оборудования')
    quantity = models.IntegerField('Количество')
    unit_price = models.DecimalField('Цена за ед.', max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Позиция документа'
        verbose_name_plural = 'Позиции документа'


class NonReturnAct(models.Model):
    deal = models.ForeignKey('deals.Deal', on_delete=models.CASCADE,
                             related_name='non_return_acts', verbose_name='Сделка')
    number = models.CharField('Номер акта', max_length=50)
    date = models.DateField('Дата', default=timezone.now)
    total_amount = models.DecimalField('Сумма к взысканию', max_digits=12, decimal_places=2, default=0)
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Акт невозврата'
        verbose_name_plural = 'Акты невозврата'
        ordering = ['-date']

    def __str__(self):
        return f'Акт невозврата №{self.number} от {self.date}'


class NonReturnActItem(models.Model):
    act = models.ForeignKey(NonReturnAct, on_delete=models.CASCADE, related_name='items')
    equipment_type = models.ForeignKey('equipment.EquipmentType', on_delete=models.PROTECT,
                                       verbose_name='Тип оборудования')
    quantity_issued = models.IntegerField('Выдано, шт')
    quantity_returned = models.IntegerField('Возвращено, шт', default=0)
    unit_price = models.DecimalField('Цена за ед.', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция акта невозврата'
        verbose_name_plural = 'Позиции акта невозврата'

    @property
    def quantity_not_returned(self):
        return self.quantity_issued - self.quantity_returned

    @property
    def total_value(self):
        return self.quantity_not_returned * float(self.unit_price)
