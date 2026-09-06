from django.contrib import admin
from .models import StgCustomerMaster, StgFinancial, StgAddress


@admin.register(StgCustomerMaster)
class StgCustomerMasterAdmin(admin.ModelAdmin):

    list_display = (
        "bp_id",
        "bp_number",
        "bp_creation_date",
        "bp_creation_source",
        "id_type",
        "id_number",
        "email",
        "mobile_number",
        "date_of_birth",
        "nationality",
        "gender",
        "contract_account",
        "contract",
        "installation",
        "move_in_date",
        "move_out_date",
    )

    search_fields = (
        "bp_id",
        "bp_number",
        "id_number",
        "email",
        "mobile_number",
        "contract_account",
        "contract",
        "installation",
    )

    list_filter = (
        "id_type",
        "bp_creation_source",
        "nationality",
        "gender",
        "bp_creation_date",
        "move_in_date",
        "move_out_date",
    )

    ordering = ("bp_id",)

    list_per_page = 50


@admin.register(StgFinancial)
class StgFinancialAdmin(admin.ModelAdmin):

    list_display = (
        "bp_id",
        "contract_account",
        "payment_date",
        "payment_amount",
    )

    search_fields = (
        "bp_id",
        "contract_account",
    )

    list_filter = (
        "payment_date",
    )

    ordering = (
        "bp_id",
        "-payment_date",
    )

    list_per_page = 50


@admin.register(StgAddress)
class StgAddressAdmin(admin.ModelAdmin):

    list_display = (
        "bp_id",
        "addr_line1",
        "addr_line2",
        "building",
        "flat",
        "street",
        "area",
        "city",
        "postal_code",
        "country",
    )

    search_fields = (
        "bp_id",
        "addr_line1",
        "addr_line2",
        "building",
        "flat",
        "street",
        "area",
        "city",
        "postal_code",
        "country",
    )

    list_filter = (
        "city",
        "area",
        "country",
    )

    ordering = (
        "bp_id",
    )

    list_per_page = 50
