from django.db import models
from django.utils import timezone


class PushCleansedData(models.Model):
    dup_member_id = models.IntegerField()
    retained_bp = models.CharField(max_length=50)
    retained_account = models.CharField(max_length=50, blank=True, null=True)
    payload_json = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("DRAFT", "Draft"),
            ("READY", "Ready"),
            ("PUSHED", "Pushed"),
            ("ERROR", "Error"),
        ],
        default="DRAFT",
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Push Payload - DupMember {self.dup_member_id} - {self.status}"