from django.contrib import admin, messages
from django.utils.html import format_html
import json

from .models import DupGroup, DupMember, PushCleansedData
from .utils import build_push_json_for_dup_member


@admin.action(description="Generate Push Cleansed Data JSON")
def generate_push_json(modeladmin, request, queryset):
    created_count = 0

    for dup_member in queryset:
        payload = build_push_json_for_dup_member(dup_member)

        PushCleansedData.objects.create(
            dup_member_id=dup_member.id,
            retained_bp=payload.get("retained_bp", ""),
            retained_account=payload.get("retained_account", ""),
            payload_json=payload,
            status="READY"
        )
        created_count += 1

    modeladmin.message_user(
        request,
        f"{created_count} push payload(s) generated successfully.",
        level=messages.SUCCESS
    )


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "id_type", "id_number", "dup_count", "created_at")


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = ("group", "bp_id", "score_total", "retain_candidate")
    actions = [generate_push_json]


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = (
        "dup_member_id",
        "retained_bp",
        "retained_account",
        "status",
        "created_at",
    )
    readonly_fields = ("payload_pretty", "created_at")
    fields = (
        "dup_member_id",
        "retained_bp",
        "retained_account",
        "status",
        "payload_json",
        "payload_pretty",
        "created_at",
    )

    def payload_pretty(self, obj):
        return format_html(
            "<pre style='white-space: pre-wrap; font-size:13px;'>{}</pre>",
            json.dumps(obj.payload_json, indent=2)
        )
    payload_pretty.short_description = "JSON Preview"