from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Fieldset
from .models import OurLegalEntity, ContractTemplate, GeneratedContract


class OurLegalEntityForm(forms.ModelForm):
    class Meta:
        model = OurLegalEntity
        fields = [
            'entity_type', 'name', 'is_default', 'phone', 'email', 'address', 'city', 'notes',
            'passport_series', 'passport_number', 'passport_issued_by',
            'passport_issued_date', 'birth_date', 'registration_address',
            'company_full_name', 'inn', 'kpp', 'ogrn', 'director', 'director_short',
            'director_title', 'legal_address',
            'bank_name', 'bank_account', 'bank_bik', 'bank_corr_account',
        ]
        widgets = {
            'passport_issued_date': forms.DateInput(attrs={'type': 'date'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2}),
            'registration_address': forms.Textarea(attrs={'rows': 2}),
            'legal_address': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('entity_type', css_class='col-md-4'),
                Column('name', css_class='col-md-6'),
                Column('is_default', css_class='col-md-2'),
            ),
            Row(
                Column('phone', css_class='col-md-4'),
                Column('email', css_class='col-md-4'),
                Column('city', css_class='col-md-4'),
            ),
            'address',
            'notes',
            Fieldset('Физическое лицо / ИП',
                Row(
                    Column('passport_series', css_class='col-md-3'),
                    Column('passport_number', css_class='col-md-3'),
                    Column('birth_date', css_class='col-md-3'),
                    Column('passport_issued_date', css_class='col-md-3'),
                ),
                'passport_issued_by',
                'registration_address',
                css_id='individual-org-fields',
            ),
            Fieldset('Юридическое лицо',
                'company_full_name',
                Row(
                    Column('inn', css_class='col-md-3'),
                    Column('kpp', css_class='col-md-3'),
                    Column('ogrn', css_class='col-md-3'),
                ),
                Row(
                    Column('director', css_class='col-md-6'),
                    Column('director_short', css_class='col-md-3'),
                    Column('director_title', css_class='col-md-3'),
                ),
                'legal_address',
                Row(
                    Column('bank_name', css_class='col-md-6'),
                    Column('bank_bik', css_class='col-md-3'),
                ),
                Row(
                    Column('bank_account', css_class='col-md-6'),
                    Column('bank_corr_account', css_class='col-md-6'),
                ),
                css_id='company-org-fields',
            ),
            Submit('submit', 'Сохранить', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">Отмена</a>'),
        )


class ContractTemplateForm(forms.ModelForm):
    class Meta:
        model = ContractTemplate
        fields = ['name', 'slug', 'body', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 16, 'class': 'font-monospace'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('name', css_class='col-md-8'), Column('slug', css_class='col-md-4')),
            'is_active',
            'body',
            Submit('submit', 'Сохранить', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">Отмена</a>'),
        )


class GeneratedContractForm(forms.ModelForm):
    class Meta:
        model = GeneratedContract
        fields = ['client', 'our_entity', 'template', 'deal', 'number', 'contract_date', 'notes']
        widgets = {'contract_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deal'].required = False
        self.fields['deal'].queryset = self.fields['deal'].queryset.select_related('client')
        self.fields['template'].queryset = ContractTemplate.objects.filter(
            is_active=True, document_type='contract'
        )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Column('client', css_class='col-md-6'), Column('our_entity', css_class='col-md-6')),
            Row(Column('template', css_class='col-md-8'), Column('deal', css_class='col-md-4')),
            Row(Column('number', css_class='col-md-4'), Column('contract_date', css_class='col-md-4')),
            'notes',
            Submit('submit', 'Сформировать договор', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">Отмена</a>'),
        )

    def clean(self):
        cleaned = super().clean()
        client = cleaned.get('client')
        deal = cleaned.get('deal')
        if client and deal and deal.client_id != client.pk:
            raise forms.ValidationError('Выбранная сделка принадлежит другому клиенту.')
        return cleaned
