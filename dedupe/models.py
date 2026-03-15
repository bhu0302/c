from django.db import models

# Create your models here.
from django.db import models

class DupGroup(models.Model):
    id_type = models.CharField(max_length=50)
    id_number = models.CharField(max_length=100)
    dup_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

class DupMember(models.Model):
    group = models.ForeignKey(DupGroup, on_delete=models.CASCADE)
    bp_id = models.CharField(max_length=50)

    score_total = models.FloatField(default=0)
    retain_candidate = models.BooleanField(default=False)
    reasons_json = models.JSONField(null=True, blank=True)
    

from django.utils import timezone


class PushCleansedData(models.Model):
    dup_member_id = models.IntegerField()
    retained_bp = models.CharField(max_length=50)
    retained_account = models.CharField(max_length=50, blank=True, null=True)
    push_message = models.TextField(blank=True, null=True)
    pushed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
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
    

