from django.contrib import admin
from .models import (
    TicketRecord,
    TicketSLARule,
    TicketAuditResult
)


@admin.register(TicketRecord)
class TicketRecordAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_number",
        "ticket_type",
        "ticket_status",
        "bp_id",
        "creation_date",
        "completion_date",
        "resolution_days",
    )

    search_fields = (
        "ticket_number",
        "bp_id",
    )

    list_filter = (
        "ticket_type",
        "ticket_status",
    )


@admin.register(TicketSLARule)
class TicketSLARuleAdmin(admin.ModelAdmin):
    list_display = (
        "ticket_type",
        "sla_days",
        "is_active",
    )


@admin.register(TicketAuditResult)
class TicketAuditResultAdmin(admin.ModelAdmin):
    list_display = (
        "ticket",
        "sla_days",
        "actual_days",
        "is_breached",
        "created_at",
    )

    list_filter = ("is_breached",)