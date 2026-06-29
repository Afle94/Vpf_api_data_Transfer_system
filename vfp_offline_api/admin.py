from django.contrib import admin
from vfp_offline_api.models import Spsales

# Register your models here.
class SpsalesAdmin(admin.ModelAdmin):
    list_display = ('Voucher_no', 'Vtype', 'invoice_no', 'Acno', 'Trandate', 'Recdate', 'Amount', 'Net_Amount', 'Mobile_no')
    search_fields = ('Voucher_no', 'Vtype', 'invoice_no', 'Acno', 'Trandate', 'Recdate', 'Amount', 'Net_Amount', 'Mobile_no')
    list_filter = ('Vtype', 'Trandate', 'Recdate')

admin.site.register(Spsales, SpsalesAdmin)
