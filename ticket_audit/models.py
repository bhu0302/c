from django.db import models


class TicketRecord(models.Model):
    ticket_number = models.CharField(max_length=100, unique=True)

    ticket_type = models.CharField(max_length=100)
    ticket_status = models.CharField(max_length=50)

    bp_id = models.CharField(max_length=100, blank=True, null=True)

    creation_date = models.DateTimeField()
    completion_date = models.DateTimeField(blank=True, null=True)

    priority = models.CharField(max_length=50, blank=True, null=True)

    def resolution_days(self):
        if self.creation_date and self.completion_date:
            return (
                self.completion_date.date() -
                self.creation_date.date()
            ).days
        return None

    def __str__(self):
        return self.ticket_number


class TicketSLARule(models.Model):
    ticket_type = models.CharField(max_length=100)
    sla_days = models.IntegerField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.ticket_type} - {self.sla_days} days"


class TicketAuditResult(models.Model):
    ticket = models.ForeignKey(
        TicketRecord,
        on_delete=models.CASCADE
    )

    sla_days = models.IntegerField()
    actual_days = models.IntegerField()

    is_breached = models.BooleanField(default=False)

    audit_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ticket.ticket_number