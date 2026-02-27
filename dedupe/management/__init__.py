from django.core.management.base import BaseCommand
from ingestion.models import StgCustomerMaster, StgFinancial
from dedupe.models import DupGroup, DupMember
from django.db.models import Count, Sum
import re

def norm_id(s):
    if not s: return ""
    return re.sub(r"[^0-9A-Za-z]", "", s.strip())

class Command(BaseCommand):
    help = "Find duplicate BPs by (id_type + id_number), score and recommend retain BP."

    def handle(self, *args, **kwargs):
        DupMember.objects.all().delete()
        DupGroup.objects.all().delete()

        # Group duplicates
        qs = (
            StgCustomerMaster.objects
            .exclude(id_type__isnull=True).exclude(id_number__isnull=True)
            .values("id_type", "id_number")
            .annotate(cnt=Count("bp_id", distinct=True))
            .filter(cnt__gt=1)
        )

        for g in qs:
            group = DupGroup.objects.create(
                id_type=g["id_type"], id_number=g["id_number"], dup_count=g["cnt"]
            )

            members = (
                StgCustomerMaster.objects
                .filter(id_type=g["id_type"], id_number=g["id_number"])
                .values("bp_id")
                .distinct()
            )

            # Precompute payments by BP
            pay = (
                StgFinancial.objects
                .values("bp_id")
                .annotate(total=Sum("payment_amount"), cnt=Count("id"))
            )
            pay_map = {p["bp_id"]: p for p in pay}

            scored = []
            for m in members:
                bp = m["bp_id"]
                p = pay_map.get(bp, {"total": 0, "cnt": 0})
                score = float(p["total"] or 0) * 0.0001 + float(p["cnt"] or 0)  # simple MVP scoring
                reasons = {"payment_total": float(p["total"] or 0), "payment_count": int(p["cnt"] or 0)}
                scored.append((bp, score, reasons))

            scored.sort(key=lambda x: x[1], reverse=True)
            retained_bp = scored[0][0]

            for bp, score, reasons in scored:
                DupMember.objects.create(
                    group=group,
                    bp_id=bp,
                    score_total=score,
                    retain_candidate=(bp == retained_bp),
                    reasons_json=reasons,
                )

        self.stdout.write(self.style.SUCCESS("✅ Dedupe completed"))