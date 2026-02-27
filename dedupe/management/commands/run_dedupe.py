from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max, Min
from ingestion.models import StgCustomerMaster, StgFinancial, StgAddress
from dedupe.models import DupGroup, DupMember


class Command(BaseCommand):
    help = "Enterprise Business Scoring for Duplicate BP Retention"

    def handle(self, *args, **kwargs):

        self.stdout.write("🔄 Running Enterprise Business Scoring...")

        DupMember.objects.all().delete()
        DupGroup.objects.all().delete()

        duplicate_groups = (
            StgCustomerMaster.objects
            .exclude(id_type__isnull=True)
            .exclude(id_number__isnull=True)
            .values("id_type", "id_number")
            .annotate(bp_count=Count("bp_id", distinct=True))
            .filter(bp_count__gt=1)
        )

        for group in duplicate_groups:

            id_type = group["id_type"]
            id_number = group["id_number"]

            dup_group = DupGroup.objects.create(
                id_type=id_type,
                id_number=id_number,
                dup_count=group["bp_count"],
            )

            members = StgCustomerMaster.objects.filter(
                id_type=id_type,
                id_number=id_number
            )

            # Identify oldest and most recent
            oldest_date = members.aggregate(Min("bp_creation_date"))["bp_creation_date__min"]
            recent_movein = members.aggregate(Max("move_in_date"))["move_in_date__max"]

            scored_members = []

            for member in members:

                score = 0
                reasons = {}

                bp_id = member.bp_id

                # -----------------------------
                # 1️⃣ Active Installation
                # -----------------------------
                active_install = member.move_out_date is None
                if active_install:
                    score += 40
                    reasons["active_installation"] = 40
                else:
                    reasons["active_installation"] = 0

                # -----------------------------
                # 2️⃣ Active Contract (simplified)
                # -----------------------------
                contract_count = StgCustomerMaster.objects.filter(
                    bp_id=bp_id
                ).values("contract").distinct().count()

                contract_score = contract_count * 10
                score += contract_score
                reasons["contract_score"] = contract_score

                # -----------------------------
                # 3️⃣ Most Recent Move-in
                # -----------------------------
                if member.move_in_date == recent_movein:
                    score += 15
                    reasons["recent_movein"] = 15
                else:
                    reasons["recent_movein"] = 0

                # -----------------------------
                # 4️⃣ Oldest BP Creation
                # -----------------------------
                if member.bp_creation_date == oldest_date:
                    score += 10
                    reasons["oldest_bp_bonus"] = 10
                else:
                    reasons["oldest_bp_bonus"] = 0

                # -----------------------------
                # 5️⃣ Profile Completeness
                # -----------------------------
                completeness_fields = [
                    member.email,
                    member.mobile_number,
                    member.date_of_birth,
                    member.nationality,
                    member.gender,
                ]

                completeness_score = sum(1 for f in completeness_fields if f) * 2

                if completeness_score >= 8:
                    score += 10
                    reasons["profile_completeness"] = 10
                else:
                    reasons["profile_completeness"] = completeness_score

                # -----------------------------
                # 6️⃣ Address Consistency
                # -----------------------------
                addresses = StgAddress.objects.filter(bp_id=bp_id)
                group_addresses = StgAddress.objects.filter(
                    bp_id__in=members.values_list("bp_id", flat=True)
                )

                addr_set = set(
                    (a.street, a.area, a.city, a.postal_code)
                    for a in group_addresses
                )

                if len(addr_set) == 1:
                    score += 5
                    reasons["address_consistency"] = 5
                else:
                    reasons["address_consistency"] = 0

                # -----------------------------
                # 7️⃣ Weighted Financial Score
                # -----------------------------
                fin = StgFinancial.objects.filter(bp_id=bp_id).aggregate(
                    total=Sum("payment_amount"),
                    count=Count("id")
                )

                total_payment = float(fin["total"] or 0)
                payment_count = int(fin["count"] or 0)

                financial_score = (total_payment * 0.001) + (payment_count * 2)

                score += financial_score
                reasons["financial_score"] = round(financial_score, 2)

                # -----------------------------
                scored_members.append((bp_id, score, reasons))

            # Sort by score descending
            scored_members.sort(key=lambda x: x[1], reverse=True)

            retained_bp = scored_members[0][0]

            for bp_id, score, reasons in scored_members:
                DupMember.objects.create(
                    group=dup_group,
                    bp_id=bp_id,
                    score_total=round(score, 2),
                    retain_candidate=(bp_id == retained_bp),
                    reasons_json=reasons,
                )

        self.stdout.write(self.style.SUCCESS("✅ Enterprise Scoring Completed"))