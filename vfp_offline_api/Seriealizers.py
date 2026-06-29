from rest_framework import serializers
from vfp_offline_api.models import Spsales


class VfpDateField(serializers.DateField):
    def to_internal_value(self, value):
        if isinstance(value, str):
            cleaned_value = value.strip()
            without_spaces = cleaned_value.replace(' ', '')
            if cleaned_value == '' or set(without_spaces) <= {'/'}:
                return None
        return super().to_internal_value(value)


class SpsalesSerializer(serializers.ModelSerializer):
    field_aliases = {
        'Voucherno': 'Voucher_no',
        'VoucherNo': 'Voucher_no',
        'voucherno': 'Voucher_no',
        'invoiceno': 'invoice_no',
        'InvoiceNo': 'invoice_no',
        'NetAmt': 'Net_Amount',
        'netamt': 'Net_Amount',
        'Mobile': 'Mobile_no',
        'mobile': 'Mobile_no',
    }

    Trandate = VfpDateField(
        input_formats=['%m/%d/%y', '%m/%d/%Y', '%d/%m/%y', '%d/%m/%Y'],
        format='%d/%m/%y',
        required=False,
        allow_null=True,
    )
    Recdate = VfpDateField(
        input_formats=['%m/%d/%y', '%m/%d/%Y', '%d/%m/%y', '%d/%m/%Y'],
        format='%d/%m/%y',
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Spsales
        fields = '__all__'
        extra_kwargs = {
            'Voucher_no': {'validators': []},
        }

    def to_internal_value(self, data):
        if hasattr(data, 'copy'):
            data = data.copy()
            for alias, field_name in self.field_aliases.items():
                if alias in data and field_name not in data:
                    data[field_name] = data[alias]
        return super().to_internal_value(data)

    def create(self, validated_data):
        voucher_no = validated_data.get('Voucher_no')
        if voucher_no:
            defaults = validated_data.copy()
            defaults.pop('Voucher_no', None)
            obj, _ = Spsales.objects.update_or_create(
                Voucher_no=voucher_no,
                defaults=defaults,
            )
            return obj
        return super().create(validated_data)
