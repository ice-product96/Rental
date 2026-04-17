from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, HTML, Fieldset
from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'client_type', 'name', 'phone', 'email', 'address', 'city', 'notes',
            # individual
            'passport_series', 'passport_number', 'passport_issued_by',
            'passport_issued_date', 'birth_date', 'registration_address',
            # company
            'company_full_name', 'inn', 'kpp', 'ogrn',
            'director', 'director_short', 'director_title', 'legal_address',
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
                Column('client_type', css_class='col-md-4'),
                Column('name', css_class='col-md-8'),
            ),
            Row(
                Column('phone', css_class='col-md-4'),
                Column('email', css_class='col-md-4'),
                Column('city', css_class='col-md-4'),
            ),
            'address',
            'notes',
            Fieldset('Физическое лицо',
                Row(
                    Column('passport_series', css_class='col-md-3'),
                    Column('passport_number', css_class='col-md-3'),
                    Column('birth_date', css_class='col-md-3'),
                    Column('passport_issued_date', css_class='col-md-3'),
                ),
                'passport_issued_by',
                'registration_address',
                css_id='individual-fields',
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
                css_id='company-fields',
            ),
            Submit('submit', 'Сохранить', css_class='btn btn-primary me-2'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">Отмена</a>'),
        )
