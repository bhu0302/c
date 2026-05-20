from django.apps import AppConfig


class TicketAuditConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ticket_audit"
    verbose_name = "Regulatory Ticket & SLA Audit Module"