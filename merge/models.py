from django.db import models

# Create your models here.
from django.db import models
from dedupe.models import DupGroup

class MergePlan(models.Model):
    group = models.ForeignKey(DupGroup, on_delete=models.CASCADE)

    retained_bp = models.CharField(max_length=50)
    bp_to_merge = models.CharField(max_length=50)

    proposed_new_ca = models.CharField(max_length=50, null=True, blank=True)
    actions_json = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=20, default="Draft")  # Draft/Approved/Executed/Rejected
    approved_by = models.CharField(max_length=100, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)