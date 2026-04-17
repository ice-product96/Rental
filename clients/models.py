from django.db import models


class Client(models.Model):
    CLIENT_TYPE_CHOICES = [
        ('individual', 'Физическое лицо'),
        ('company', 'Юридическое лицо'),
    ]

    client_type = models.CharField('Тип клиента', max_length=20, choices=CLIENT_TYPE_CHOICES, default='individual')
    name = models.CharField('Имя / Наименование', max_length=255)
    phone = models.CharField('Телефон', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    address = models.TextField('Адрес', blank=True)
    city = models.CharField('Город', max_length=100, default='Екатеринбург')
    notes = models.TextField('Примечания', blank=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    # Physical person fields
    passport_series = models.CharField('Серия паспорта', max_length=10, blank=True)
    passport_number = models.CharField('Номер паспорта', max_length=20, blank=True)
    passport_issued_by = models.CharField('Кем выдан', max_length=255, blank=True)
    passport_issued_date = models.DateField('Дата выдачи', null=True, blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    registration_address = models.TextField('Адрес регистрации', blank=True)

    # Legal entity fields
    company_full_name = models.CharField('Полное наименование', max_length=500, blank=True)
    inn = models.CharField('ИНН', max_length=20, blank=True)
    kpp = models.CharField('КПП', max_length=20, blank=True)
    ogrn = models.CharField('ОГРН', max_length=20, blank=True)
    director = models.CharField('Руководитель (ФИО)', max_length=255, blank=True)
    director_short = models.CharField('Руководитель (И.О. Фамилия)', max_length=100, blank=True)
    director_title = models.CharField('Должность руководителя', max_length=100, default='Директор', blank=True)
    legal_address = models.TextField('Юридический адрес', blank=True)
    bank_name = models.CharField('Банк', max_length=255, blank=True)
    bank_account = models.CharField('Расчётный счёт', max_length=30, blank=True)
    bank_bik = models.CharField('БИК', max_length=20, blank=True)
    bank_corr_account = models.CharField('Корр. счёт', max_length=30, blank=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def is_company(self):
        return self.client_type == 'company'

    @property
    def type_label(self):
        return 'Юр. лицо' if self.is_company else 'Физ. лицо'

    @property
    def deals_count(self):
        return self.deals.count()

    @property
    def active_deals_count(self):
        return self.deals.filter(status__in=['rented', 'delivery', 'partial_return']).count()
