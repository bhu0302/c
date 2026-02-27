from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import StgCustomerMaster, StgFinancial, StgAddress


@admin.register(StgCustomerMaster)
class StgCustomerMasterAdmin(admin.ModelAdmin):
    list_display = (
        "bp_id", "id_type", "id_number", "email", "mobile_number",
        "contract_account", "installation", "move_in_date", "move_out_date",
        "bp_creation_date", "bp_creation_source",
    )
    search_fields = ("bp_id", "id_number", "email", "mobile_number", "contract_account", "installation")
    list_filter = ("id_type", "bp_creation_source", "nationality", "gender")
    list_per_page = 50


@admin.register(StgFinancial)
class StgFinancialAdmin(admin.ModelAdmin):
    list_display = ("bp_id", "contract_account", "payment_date", "payment_amount")
    search_fields = ("bp_id", "contract_account")
    list_filter = ("payment_date",)
    list_per_page = 50


@admin.register(StgAddress)
class StgAddressAdmin(admin.ModelAdmin):
    list_display = ("bp_id", "addr_line1", "street", "area", "city", "postal_code", "country")
    search_fields = ("bp_id", "addr_line1", "street", "area", "city", "postal_code")
    list_filter = ("city", "area", "country")
    list_per_page = 50