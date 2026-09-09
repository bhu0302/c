
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Sum, Max, Min

from ingestion.models import (
    StgCustomerMaster,
    StgFinancial,
    StgAddress,
)

from dedupe.models import DupGroup, DupMember


class Command(BaseCommand):

    help = "Enterprise Business Scoring for Duplicate BP Retention"

    def handle(self, *args, **kwargs):

        self.stdout.write(
            "🔄 Running Enterprise Business Scoring..."
        )

        # ---------------------------------------------------------
        # Rebuild deduplication result using latest staging data
        # ---------------------------------------------------------
        with transaction.atomic():

            DupMember.objects.all().delete()
            DupGroup.objects.all().delete()

            # -----------------------------------------------------
            # Identify duplicate identity groups
            # Same ID Type + ID Number with more than one BP
            # -----------------------------------------------------
            duplicate_groups = (
                StgCustomerMaster.objects
                .exclude(id_type__isnull=True)
                .exclude(id_number__isnull=True)
                .exclude(id_type="")
                .exclude(id_number="")
                .values(
                    "id_type",
                    "id_number"
                )
                .annotate(
                    bp_count=Count(
                        "bp_id",
                        distinct=True
                    )
                )
                .filter(
                    bp_count__gt=1
                )
            )

            total_groups = 0
            total_members = 0

            for group in duplicate_groups:

                id_type = group["id_type"]
                id_number = group["id_number"]

                # -------------------------------------------------
                # Get all records belonging to this identity
                # -------------------------------------------------
                members = (
                    StgCustomerMaster.objects
                    .filter(
                        id_type=id_type,
                        id_number=id_number
                    )
                    .exclude(bp_id__isnull=True)
                    .exclude(bp_id="")
                )

                # -------------------------------------------------
                # Distinct BP IDs in the duplicate group
                # -------------------------------------------------
                bp_ids = list(
                    members
                    .values_list(
                        "bp_id",
                        flat=True
                    )
                    .distinct()
                )

                if len(bp_ids) <= 1:
                    continue

                # -------------------------------------------------
                # Create duplicate group
                # -------------------------------------------------
                dup_group = DupGroup.objects.create(
                    id_type=id_type,
                    id_number=id_number,
                    dup_count=len(bp_ids),
                )

                total_groups += 1

                # -------------------------------------------------
                # Group-level dates
                # -------------------------------------------------
                oldest_date = members.aggregate(
                    Min("bp_creation_date")
                )["bp_creation_date__min"]

                recent_movein = members.aggregate(
                    Max("move_in_date")
                )["move_in_date__max"]

                # -------------------------------------------------
                # Address consistency for complete duplicate group
                # -------------------------------------------------
                group_addresses = StgAddress.objects.filter(
                    bp_id__in=bp_ids
                )

                addr_set = set(
                    (
                        a.street,
                        a.area,
                        a.city,
                        a.postal_code
                    )
                    for a in group_addresses
                    if any([
                        a.street,
                        a.area,
                        a.city,
                        a.postal_code
                    ])
                )

                address_consistent = (
                    len(addr_set) == 1
                    and len(addr_set) > 0
                )

                scored_members = []

                # -------------------------------------------------
                # Score one time per BP
                # -------------------------------------------------
                for bp_id in bp_ids:

                    # -------------------------------------------------
                    # A BP may have multiple customer-master rows.
                    # Prefer active/latest record for display fields.
                    # -------------------------------------------------
                    bp_records = (
                        members
                        .filter(bp_id=bp_id)
                        .order_by(
                            "move_out_date",
                            "-move_in_date",
                            "-bp_creation_date",
                            "-id",
                        )
                    )

                    member = bp_records.first()

                    if not member:
                        continue

                    score = 0
                    reasons = {}

                    # =================================================
                    # 1. ACTIVE INSTALLATION
                    # =================================================
                    active_install = bp_records.filter(
                        move_out_date__isnull=True
                    ).exists()

                    if active_install:
                        score += 40
                        reasons["active_installation"] = 40
                    else:
                        reasons["active_installation"] = 0

                    # =================================================
                    # 2. ACTIVE / DISTINCT CONTRACT SCORE
                    # =================================================
                    contract_count = (
                        StgCustomerMaster.objects
                        .filter(bp_id=bp_id)
                        .exclude(contract__isnull=True)
                        .exclude(contract="")
                        .values("contract")
                        .distinct()
                        .count()
                    )

                    contract_score = contract_count * 10

                    score += contract_score

                    reasons["contract_score"] = contract_score
                    reasons["contract_count"] = contract_count

                    # =================================================
                    # 3. MOST RECENT MOVE-IN
                    # =================================================
                    bp_recent_movein = bp_records.aggregate(
                        Max("move_in_date")
                    )["move_in_date__max"]

                    if (
                        recent_movein is not None
                        and
                        bp_recent_movein == recent_movein
                    ):

                        score += 15
                        reasons["recent_movein"] = 15

                    else:
                        reasons["recent_movein"] = 0

                    # =================================================
                    # 4. OLDEST BP CREATION DATE
                    # =================================================
                    bp_oldest_date = bp_records.aggregate(
                        Min("bp_creation_date")
                    )["bp_creation_date__min"]

                    if (
                        oldest_date is not None
                        and
                        bp_oldest_date == oldest_date
                    ):

                        score += 10
                        reasons["oldest_bp_bonus"] = 10

                    else:
                        reasons["oldest_bp_bonus"] = 0

                    # =================================================
                    # 5. PROFILE COMPLETENESS
                    # =================================================
                    completeness_fields = [
                        member.email,
                        member.mobile_number,
                        member.date_of_birth,
                        member.nationality,
                        member.gender,
                    ]

                    available_fields = sum(
                        1
                        for value in completeness_fields
                        if value
                    )

                    completeness_score = available_fields * 2

                    if completeness_score >= 8:

                        score += 10
                        reasons["profile_completeness"] = 10

                    else:

                        score += completeness_score
                        reasons[
                            "profile_completeness"
                        ] = completeness_score

                    # =================================================
                    # 6. ADDRESS CONSISTENCY
                    # =================================================
                    if address_consistent:

                        score += 5
                        reasons["address_consistency"] = 5

                    else:

                        reasons["address_consistency"] = 0

                    # =================================================
                    # 7. WEIGHTED FINANCIAL SCORE
                    # =================================================
                    fin = (
                        StgFinancial.objects
                        .filter(bp_id=bp_id)
                        .aggregate(
                            total=Sum("payment_amount"),
                            count=Count("id")
                        )
                    )

                    total_payment = float(
                        fin["total"] or 0
                    )

                    payment_count = int(
                        fin["count"] or 0
                    )

                    financial_score = (
                        total_payment * 0.001
                    ) + (
                        payment_count * 2
                    )

                    score += financial_score

                    reasons["financial_score"] = round(
                        financial_score,
                        2
                    )

                    reasons["total_payment"] = round(
                        total_payment,
                        2
                    )

                    reasons["payment_count"] = payment_count

                    # =================================================
                    # Keep member record so important SAP fields can
                    # be transferred into DupMember
                    # =================================================
                    scored_members.append({
                        "member": member,
                        "bp_id": bp_id,
                        "score": round(score, 2),
                        "reasons": reasons,
                    })

                # -------------------------------------------------
                # Highest score first
                #
                # Tie breaker:
                # BP ID used for deterministic selection
                # -------------------------------------------------
                scored_members.sort(
                    key=lambda x: (
                        -x["score"],
                        str(x["bp_id"])
                    )
                )

                if not scored_members:
                    dup_group.delete()
                    continue

                retained_bp = scored_members[0]["bp_id"]

                # -------------------------------------------------
                # Create DupMember records
                # -------------------------------------------------
                for result in scored_members:

                    member = result["member"]
                    bp_id = result["bp_id"]
                    score = result["score"]
                    reasons = result["reasons"]

                    DupMember.objects.create(
                        group=dup_group,

                        bp_id=bp_id,

                        installation=member.installation,

                        contract_account=member.contract_account,

                        contract=member.contract,

                         account_class=None,

                        score_total=score,

                        retain_candidate=(
                            bp_id == retained_bp
                        ),

                        reasons_json=reasons,
                    )

                    total_members += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Enterprise Scoring Completed | "
                f"Duplicate Groups: {total_groups} | "
                f"Duplicate BPs: {total_members}"
            )
        )

