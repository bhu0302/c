import json
from django.contrib import admin
from django.utils.html import format_html

from .models import DupGroup, DupMember, PushCleansedData


def parse_reason_json(value):
    if not value:
        return {}

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return {}

    return {}


class DupMemberInline(admin.TabularInline):
    model = DupMember
    extra = 0
    fields = (
        "bp_number",
        "bp_name",
        "is_retained",
        "score",
        "score_breakdown_display",
    )
    readonly_fields = (
        "bp_number",
        "bp_name",
        "is_retained",
        "score",
        "score_breakdown_display",
    )

    def score_breakdown_display(self, obj):
        data = parse_reason_json(obj.reason_json)

        ai = data.get("active_installation", 0)
        c = data.get("contract_score", 0)
        m = data.get("recent_movein", 0)
        o = data.get("oldest_bp_bonus", 0)
        p = data.get("profile_completeness", 0)
        a = data.get("address_consistency", 0)
        f = data.get("financial_score", 0)

        return (
            f"AI:{ai} | C:{c} | M:{m} | "
            f"O:{o} | P:{p} | A:{a} | F:{f}"
        )

    score_breakdown_display.short_description = "Score Breakdown"


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "group_name", "created_at")
    inlines = [DupMemberInline]


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "dup_group",
        "bp_number",
        "bp_name",
        "is_retained",
        "score",
        "score_breakdown_display",
    )
    readonly_fields = ("score_breakdown_display",)

    def score_breakdown_display(self, obj):
        data = parse_reason_json(obj.reason_json)

        ai = data.get("active_installation", 0)
        c = data.get("contract_score", 0)
        m = data.get("recent_movein", 0)
        o = data.get("oldest_bp_bonus", 0)
        p = data.get("profile_completeness", 0)
        a = data.get("address_consistency", 0)
        f = data.get("financial_score", 0)

        return format_html(
            "<b>AI</b>: {} | <b>C</b>: {} | <b>M</b>: {} | "
            "<b>O</b>: {} | <b>P</b>: {} | <b>A</b>: {} | <b>F</b>: {}",
            ai, c, m, o, p, a, f
        )

    score_breakdown_display.short_description = "Score Breakdown"


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "push_message", "created_at")
    readonly_fields = ("created_at",)