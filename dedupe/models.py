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