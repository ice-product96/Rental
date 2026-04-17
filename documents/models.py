from django.db import models


class OurLegalEntity(models.Model):
    """Реквизиты исполнителя (наша сторона в договоре): юр. лицо или физ. лицо / ИП."""

    ENTITY_TYPE_CHOICES = [
        ('individual', 'Физическое лицо / ИП'),
        ('company', 'Юридическое лицо'),
    ]

    entity_type = models.CharField('Тип', max_length=20, choices=ENTITY_TYPE_CHOICES, default='company')
    name = models.CharField('Краткое наименование / ФИО', max_length=255)
    is_default = models.BooleanField('Использовать по умолчанию', default=False)

    phone = models.CharField('Телефон', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Почтовый адрес', blank=True)
    city = models.CharField('Город', max_length=100, default='Екатеринбург', blank=True)
    notes = models.TextField('Примечания', blank=True)

    passport_series = models.CharField('Серия паспорта', max_length=10, blank=True)
    passport_number = models.CharField('Номер паспорта', max_length=20, blank=True)
    passport_issued_by = models.CharField('Кем выдан', max_length=255, blank=True)
    passport_issued_date = models.DateField('Дата выдачи паспорта', null=True, blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    registration_address = models.TextField('Адрес регистрации', blank=True)

    company_full_name = models.CharField('Полное наименование', max_length=500, blank=True)
    inn = models.CharField('ИНН', max_length=20, blank=True)
    kpp = models.CharField('КПП', max_length=20, blank=True)
    ogrn = models.CharField('ОГРН / ОГРНИП', max_length=20, blank=True)
    director = models.CharField('Подписант (ФИО полностью)', max_length=255, blank=True)
    director_short = models.CharField('Подписант (И.О. Фамилия)', max_length=100, blank=True)
    director_title = models.CharField('Должность подписанта', max_length=100, default='Директор', blank=True)
    legal_address = models.TextField('Юридический адрес', blank=True)
    bank_name = models.CharField('Банк', max_length=255, blank=True)
    bank_account = models.CharField('Расчётный счёт', max_length=30, blank=True)
    bank_bik = models.CharField('БИК', max_length=20, blank=True)
    bank_corr_account = models.CharField('Корр. счёт', max_length=30, blank=True)

    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Наше юр. лицо / ИП'
        verbose_name_plural = 'Наши юр. лица и ИП'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name

    @property
    def is_company(self):
        return self.entity_type == 'company'

    def save(self, *args, **kwargs):
        if self.is_default:
            OurLegalEntity.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ContractTemplate(models.Model):
    """Шаблон документа (Django Template: переменные зависят от типа документа)."""

    DOCUMENT_TYPE_CHOICES = [
        ('contract', 'Договор'),
        ('invoice', 'Счёт'),
        ('act', 'Акт'),
    ]

    name = models.CharField('Название шаблона', max_length=200)
    slug = models.SlugField('Код', max_length=80, unique=True)
    document_type = models.CharField('Тип документа', max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='contract')
    body = models.TextField(
        'Текст шаблона',
        help_text='Синтаксис Django Template: переменные зависят от типа документа.',
    )
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Шаблон документа'
        verbose_name_plural = 'Шаблоны документов'
        ordering = ['document_type', 'name']

    def __str__(self):
        return f'{self.get_document_type_display()}: {self.name}'


class GeneratedContract(models.Model):
    """Сгенерированный договор, привязанный к клиенту (и опционально к сделке)."""

    client = models.ForeignKey(
        'clients.Client', on_delete=models.PROTECT,
        related_name='generated_contracts', verbose_name='Клиент',
    )
    our_entity = models.ForeignKey(
        OurLegalEntity, on_delete=models.PROTECT,
        related_name='generated_contracts', verbose_name='Наше юр. лицо',
    )
    template = models.ForeignKey(
        ContractTemplate, on_delete=models.PROTECT,
        related_name='generated_contracts', verbose_name='Шаблон',
    )
    deal = models.ForeignKey(
        'deals.Deal', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='generated_contracts', verbose_name='Сделка',
    )

    number = models.CharField('Номер договора', max_length=100)
    contract_date = models.DateField('Дата договора')
    rendered_html = models.TextField('Сгенерированный текст (HTML)')
    notes = models.TextField('Комментарий', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Договор'
        verbose_name_plural = 'Договоры'
        ordering = ['-contract_date', '-created_at']

    def __str__(self):
        return f'{self.number} — {self.client.name}'
