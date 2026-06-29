from django.db import models


# Create your models here.

class Spsales(models.Model):
    Voucher_no = models.CharField(unique = True,max_length = 50,null= True,verbose_name= 'Voucher_no')
    Vtype = models.CharField(max_length = 50,verbose_name = "Voucher Type")
    invoice_no = models.CharField(max_length=50,blank = True,null = True)
    Acno = models.CharField(max_length = 50,blank=True,null= True,verbose_name = 'Account Name')
    Trandate = models.DateField(null = True,blank = True,verbose_name = "Transaction Date")
    Recdate =  models.DateField(null = True,blank = True,verbose_name = "Rec Date")
    Amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Amount")
    Net_Amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Net Amount")
    Mobile_no = models.CharField(max_length=50, blank=True, null=True,verbose_name = 'Mobile No')
