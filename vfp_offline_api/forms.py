from django import forms
from django.contrib.auth.models import User
from vfp_offline_api.models import Spsales


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class SpsalesForm(forms.ModelForm):
    class Meta:
        model = Spsales
        fields = [
            'Voucher_no',
            'Vtype',
            'invoice_no',
            'Acno',
            'Trandate',
            'Recdate',
            'Amount',
            'Net_Amount',
            'Mobile_no',
        ]
        widgets = {
            'Trandate': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'Recdate': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'field-input')
        self.fields['Trandate'].input_formats = ['%Y-%m-%d']
        self.fields['Recdate'].input_formats = ['%Y-%m-%d']
