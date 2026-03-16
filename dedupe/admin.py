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


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "score",
        "score_breakdown_display",
    )
    readonly_fields = ("score_breakdown_display",)

    def score_breakdown_display(self, obj):
        data = parse_reason_json(getattr(obj, "reason_json", None))

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
    list_display = ("id",)