from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Max, Min
from ingestion.models import StgCustomerMaster, StgFinancial, StgAddress
from dedupe.models import DupGroup, DupMember


class Command(BaseCommand):
    help = "Enterprise Business Scoring for Duplicate BP Retention"

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Running Enterprise Business Scoring...")

        # Rebuild dedupe output fresh each run
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

            oldest_date = members.aggregate(Min("bp_creation_date"))["bp_creation_date__min"]
            recent_movein = members.aggregate(Max("move_in_date"))["move_in_date__max"]

            # address consistency for whole group
            group_addresses = StgAddress.objects.filter(
                bp_id__in=members.values_list("bp_id", flat=True)
            )

            addr_set = set(
                (a.street, a.area, a.city, a.postal_code)
                for a in group_addresses
            )
            address_consistency_score = 5 if len(addr_set) == 1 and len(addr_set) > 0 else 0

            scored_members = []

            for member in members:
                score = 0
                reasons = {}

                bp_id = member.bp_id

                # 1) Active Installation
                active_install = member.move_out_date is None
                if active_install:
                    score += 40
                    reasons["active_installation"] = 40
                else:
                    reasons["active_installation"] = 0

                # 2) Active Contract
                contract_count = (
                    StgCustomerMaster.objects
                    .filter(bp_id=bp_id)
                    .exclude(contract__isnull=True)
                    .exclude(contract__exact="")
                    .values("contract")
                    .distinct()
                    .count()
                )

                contract_score = contract_count * 10
                score += contract_score
                reasons["contract_score"] = contract_score

                # 3) Most Recent Move-in
                if member.move_in_date and member.move_in_date == recent_movein:
                    score += 15
                    reasons["recent_movein"] = 15
                else:
                    reasons["recent_movein"] = 0

                # 4) Oldest BP Creation
                if member.bp_creation_date and member.bp_creation_date == oldest_date:
                    score += 10
                    reasons["oldest_bp_bonus"] = 10
                else:
                    reasons["oldest_bp_bonus"] = 0

                # 5) Profile Completeness
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
                    score += completeness_score
                    reasons["profile_completeness"] = completeness_score

                # 6) Address Consistency
                score += address_consistency_score
                reasons["address_consistency"] = address_consistency_score

                # 7) Weighted Financial Score
                fin = StgFinancial.objects.filter(bp_id=bp_id).aggregate(
                    total=Sum("payment_amount"),
                    count=Count("id")
                )

                total_payment = float(fin["total"] or 0)
                payment_count = int(fin["count"] or 0)

                financial_score = (total_payment * 0.001) + (payment_count * 2)
                score += financial_score
                reasons["financial_score"] = round(financial_score, 2)

                # account_class is not a direct field in StgCustomerMaster
                extra_attrs = member.extra_attributes or {}
                account_class = extra_attrs.get("account_class") or extra_attrs.get("class")

                scored_members.append({
                    "bp_id": bp_id,
                    "installation": member.installation,
                    "contract_account": member.contract_account,
                    "contract": member.contract,
                    "account_class": account_class,
                    "score": round(score, 2),
                    "reasons": reasons,
                })

            # Highest score retained
            scored_members.sort(key=lambda x: x["score"], reverse=True)
            retained_bp = scored_members[0]["bp_id"]

            for item in scored_members:
                DupMember.objects.create(
                    group=dup_group,
                    bp_id=item["bp_id"],
                    installation=item["installation"],
                    contract_account=item["contract_account"],
                    contract=item["contract"],
                    account_class=item["account_class"],
                    score_total=item["score"],
                    retain_candidate=(item["bp_id"] == retained_bp),
                    reasons_json=item["reasons"],
                )

        self.stdout.write(self.style.SUCCESS("✅ Enterprise Scoring Completed"))