from django.db import models

# Create your models here.
from django.db import models

class StgCustomerMaster(models.Model):
    bp_id = models.CharField(max_length=50)
    bp_creation_date = models.DateField(null=True, blank=True)
    bp_creation_source = models.CharField(max_length=50, null=True, blank=True)
    bp_number = models.CharField(max_length=50, null=True, blank=True)

    id_type = models.CharField(max_length=50, null=True, blank=True)
    id_number = models.CharField(max_length=100, null=True, blank=True)

    email = models.EmailField(null=True, blank=True)
    mobile_number = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)

    contract_account = models.CharField(max_length=50, null=True, blank=True)
    contract = models.CharField(max_length=50, null=True, blank=True)
    installation = models.CharField(max_length=50, null=True, blank=True)
    move_in_date = models.DateField(null=True, blank=True)
    move_out_date = models.DateField(null=True, blank=True)

    extra_attributes = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["id_type", "id_number"]),
            models.Index(fields=["bp_id"]),
        ]

class StgFinancial(models.Model):
    bp_id = models.CharField(max_length=50)
    contract_account = models.CharField(max_length=50, null=True, blank=True)
    payment_date = models.DateField(null=True, blank=True)
    payment_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["bp_id"]),
            models.Index(fields=["contract_account"]),
        ]

class StgAddress(models.Model):
    bp_id = models.CharField(max_length=50)

    addr_line1 = models.CharField(max_length=200, null=True, blank=True)
    addr_line2 = models.CharField(max_length=200, null=True, blank=True)
    building = models.CharField(max_length=100, null=True, blank=True)
    flat = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["bp_id"])]