from django.contrib import admin
from django.utils.html import format_html
from .models import DupGroup, DupMember, PushCleansedData


def format_reasons(reasons):
    if not reasons:
        return "-"
    return " | ".join(f"{k}:{v}" for k, v in reasons.items())


def build_push_message(retained_member):
    """
    Build a business-friendly push message for source-system action.
    """
    if not retained_member:
        return ""

    group = retained_member.group
    members = DupMember.objects.filter(group=group)

    lines = []
    lines.append(f"ID Type: {group.id_type}")
    lines.append(f"ID Number: {group.id_number}")
    lines.append(f"Retained BP: {retained_member.bp_id}")
    lines.append("")

    lines.append("Unretained BP actions:")

    found_unretained = False
    for m in members:
        if m.id == retained_member.id:
            continue

        found_unretained = True
        installation = m.installation or "-"
        contract_account = m.contract_account or "-"
        contract = m.contract or "-"

        lines.append(
            f"- DupMember {m.id} | BP {m.bp_id} | Installation {installation} | "
            f"Old CA {contract_account} | Contract {contract} | "
            f"Action: Move-out old BP, create new CA for retained BP, "
            f"move-in retained BP, merge to retained BP {retained_member.bp_id}"
        )

    if not found_unretained:
        lines.append("- No unretained BP records found.")

    return "\n".join(lines)


def build_payload_json(retained_member):
    """
    JSON payload for source-system merge / move-out / move-in processing.
    """
    if not retained_member:
        return {}

    group = retained_member.group
    members = DupMember.objects.filter(group=group)

    retained_data = {
        "dup_member_id": retained_member.id,
        "bp_id": retained_member.bp_id,
        "installation": retained_member.installation,
        "contract_account": retained_member.contract_account,
        "contract": retained_member.contract,
        "account_class": retained_member.account_class,
        "score_total": retained_member.score_total,
        "retain_candidate": retained_member.retain_candidate,
        "reasons_json": retained_member.reasons_json or {},
        "new_contract_account_required": True,
    }

    unretained_data = []

    for m in members:
        if m.id == retained_member.id:
            continue

        unretained_data.append({
            "dup_member_id": m.id,
            "bp_id": m.bp_id,
            "installation": m.installation,
            "existing_contract_account": m.contract_account,
            "contract": m.contract,
            "account_class": m.account_class,
            "score_total": m.score_total,
            "reasons_json": m.reasons_json or {},
            "action": {
                "move_out_old_bp": True,
                "create_new_ca_for_retained_bp": True,
                "move_in_retained_bp": True,
                "merge_to_retained_bp": retained_member.bp_id,
            }
        })

    payload = {
        "group_id": group.id,
        "id_type": group.id_type,
        "id_number": group.id_number,
        "process_type": "BP_MERGE_AND_INSTALLATION_TRANSFER",
        "retained": retained_data,
        "unretained": unretained_data,
        "summary": {
            "total_bps": members.count(),
            "retained_count": 1,
            "unretained_count": len(unretained_data),
        },
        "status": "READY",
    }

    return payload


class DupMemberInline(admin.TabularInline):
    model = DupMember
    extra = 0
    fields = (
        "id",
        "bp_id",
        "installation",
        "contract_account",
        "contract",
        "score_total",
        "retain_candidate",
        "score_breakdown_display",
        "add_push_link",
    )
    readonly_fields = ("id", "score_breakdown_display", "add_push_link")

    def score_breakdown_display(self, obj):
        if not obj or not obj.reasons_json:
            return "-"
        return format_reasons(obj.reasons_json)

    score_breakdown_display.short_description = "Score Breakdown"

    def add_push_link(self, obj):
        if obj and obj.retain_candidate:
            return format_html(
                '<a class="button" href="/admin/dedupe/pushcleanseddata/add/?dup_member_id={}">Add Push Cleansed Data</a>',
                obj.id
            )
        return "-"

    add_push_link.short_description = "Push Cleansed Data"


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "id_type", "id_number", "dup_count", "created_at")
    search_fields = ("id_type", "id_number")
    inlines = [DupMemberInline]


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "bp_id",
        "installation",
        "contract_account",
        "contract",
        "score_total",
        "retain_candidate",
        "score_breakdown_display",
        "push_link",
    )
    search_fields = ("bp_id", "installation", "contract_account", "contract")
    list_filter = ("retain_candidate", "group__id_type")
    readonly_fields = ("score_breakdown_display",)

    def score_breakdown_display(self, obj):
        if not obj or not obj.reasons_json:
            return "-"
        return format_reasons(obj.reasons_json)

    score_breakdown_display.short_description = "Score Breakdown"

    def push_link(self, obj):
        if obj and obj.retain_candidate:
            return format_html(
                '<a class="button" href="/admin/dedupe/pushcleanseddata/add/?dup_member_id={}">Add Push Cleansed Data</a>',
                obj.id
            )
        return "-"

    push_link.short_description = "Push Cleansed Data"


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dup_group",
        "dup_member",
        "retained_bp",
        "retained_account",
        "status",
        "short_push_message",
        "created_at",
        "updated_at",
    )

    list_filter = ("status", "dup_group__id_type", "created_at")
    search_fields = (
        "retained_bp",
        "retained_account",
        "dup_group__id_number",
        "dup_member__bp_id",
    )

    readonly_fields = ("created_at", "updated_at")

    fields = (
        "dup_group",
        "dup_member",
        "retained_bp",
        "retained_account",
        "push_message",
        "payload_json",
        "status",
        "pushed_at",
        "created_at",
        "updated_at",
    )

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)

        dup_member_id = request.GET.get("dup_member_id")
        if dup_member_id:
            try:
                retained_member = DupMember.objects.get(id=dup_member_id)

                initial["dup_group"] = retained_member.group
                initial["dup_member"] = retained_member
                initial["retained_bp"] = retained_member.bp_id
                initial["retained_account"] = retained_member.contract_account
                initial["push_message"] = build_push_message(retained_member)
                initial["payload_json"] = build_payload_json(retained_member)
                initial["status"] = "READY"
            except DupMember.DoesNotExist:
                pass

        return initial

    def save_model(self, request, obj, form, change):
        if obj.dup_member:
            retained_member = obj.dup_member

            if not obj.dup_group:
                obj.dup_group = retained_member.group

            if not obj.retained_bp:
                obj.retained_bp = retained_member.bp_id

            if not obj.retained_account:
                obj.retained_account = retained_member.contract_account

            if not obj.push_message:
                obj.push_message = build_push_message(retained_member)

            if not obj.payload_json:
                obj.payload_json = build_payload_json(retained_member)

            if obj.status == "DRAFT":
                obj.status = "READY"

        super().save_model(request, obj, form, change)

    def short_push_message(self, obj):
        if not obj.push_message:
            return "-"
        return obj.push_message[:100] + ("..." if len(obj.push_message) > 100 else "")

    short_push_message.short_description = "Push Message"