from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
import json

from .models import DupGroup, DupMember, PushCleansedData
from .utils import build_push_json_for_group


def _read_score_data(obj):
    """
    Safely read score breakdown from DupMember.
    Change the field list below if your actual score JSON field has another name.
    """
    possible_fields = [
        "score_breakdown",
        "score_details",
        "score_json",
        "scores",
        "score_components",
    ]

    raw = None
    for field in possible_fields:
        if hasattr(obj, field):
            raw = getattr(obj, field, None)
            if raw not in (None, "", {}):
                break

    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except Exception:
            return {}

    return {}


def _score_summary_html(obj):
    data = _read_score_data(obj)

    return format_html(
        "AI:{} | C:{} | M:{} | O:{} | P:{} | A:{} | F:{}",
        data.get("active_installation", 0),
        data.get("contract_score", 0),
        data.get("recent_movein", 0),
        data.get("oldest_bp_bonus", 0),
        data.get("profile_completeness", 0),
        data.get("address_consistency", 0),
        data.get("financial_score", 0),
    )


class DupMemberInline(admin.TabularInline):
    model = DupMember
    extra = 0
    can_delete = False
    show_change_link = True

    fields = (
        "bp_id",
        "score_total",
        "retain_candidate",
        "score_summary",
    )

    readonly_fields = (
        "bp_id",
        "score_total",
        "retain_candidate",
        "score_summary",
    )

    def score_summary(self, obj):
        return _score_summary_html(obj)
    score_summary.short_description = "Score Breakdown"


@admin.action(description="Prepare Push Data for selected groups")
def prepare_push_data(modeladmin, request, queryset):
    prepared = 0
    failed = 0

    for group in queryset:
        try:
            payload = build_push_json_for_group(group)

            PushCleansedData.objects.update_or_create(
                dup_group=group,
                defaults={
                    "retained_bp": payload.get("retained_bp"),
                    "retained_account": payload.get("retained_account"),
                    "payload_json": payload,
                    "status": "READY",
                }
            )
            prepared += 1

        except Exception as e:
            failed += 1
            PushCleansedData.objects.update_or_create(
                dup_group=group,
                defaults={
                    "retained_bp": None,
                    "retained_account": None,
                    "payload_json": {
                        "dup_group_id": group.id,
                        "error": str(e),
                    },
                    "status": "ERROR",
                }
            )

    if failed == 0:
        modeladmin.message_user(
            request,
            f"{prepared} selected group(s) prepared successfully.",
            level=messages.SUCCESS,
        )
    else:
        modeladmin.message_user(
            request,
            f"{prepared} prepared, {failed} failed.",
            level=messages.WARNING,
        )


@admin.action(description="Push selected groups to target")
def push_selected_groups(modeladmin, request, queryset):
    pushed = 0
    failed = 0

    for group in queryset:
        try:
            payload = build_push_json_for_group(group)

            obj, _ = PushCleansedData.objects.update_or_create(
                dup_group=group,
                defaults={
                    "retained_bp": payload.get("retained_bp"),
                    "retained_account": payload.get("retained_account"),
                    "payload_json": payload,
                    "status": "READY",
                }
            )

            # Replace this with real target push later
            obj.status = "PUSHED"
            obj.save()

            pushed += 1

        except Exception as e:
            failed += 1
            PushCleansedData.objects.update_or_create(
                dup_group=group,
                defaults={
                    "retained_bp": None,
                    "retained_account": None,
                    "payload_json": {
                        "dup_group_id": group.id,
                        "error": str(e),
                    },
                    "status": "ERROR",
                }
            )

    if failed == 0:
        modeladmin.message_user(
            request,
            f"{pushed} selected group(s) pushed successfully.",
            level=messages.SUCCESS,
        )
    else:
        modeladmin.message_user(
            request,
            f"{pushed} pushed, {failed} failed.",
            level=messages.WARNING,
        )


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "id_type",
        "id_number",
        "dup_count",
        "created_at",
        "push_data_link",
    )
    actions = [prepare_push_data, push_selected_groups]
    inlines = [DupMemberInline]

    def push_data_link(self, obj):
        try:
            if hasattr(obj, "push_data") and obj.push_data:
                return format_html(
                    '<a href="/admin/dedupe/pushcleanseddata/{}/change/">View Push Data</a>',
                    obj.push_data.id
                )
        except Exception:
            pass
        return "-"
    push_data_link.short_description = "Push Cleansed Data"


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "bp_id",
        "score_total",
        "retain_candidate",
        "score_summary",
    )
    list_filter = ("retain_candidate", "group__id_type")
    search_fields = ("bp_id", "group__id_number", "group__id_type")

    def score_summary(self, obj):
        return _score_summary_html(obj)
    score_summary.short_description = "Score Breakdown"


@admin.action(description="Push selected records")
def push_selected_records(modeladmin, request, queryset):
    pushed = 0
    failed = 0

    for obj in queryset:
        try:
            obj.status = "PUSHED"
            obj.save()
            pushed += 1
        except Exception:
            obj.status = "ERROR"
            obj.save()
            failed += 1

    if failed == 0:
        modeladmin.message_user(
            request,
            f"{pushed} record(s) pushed successfully.",
            level=messages.SUCCESS,
        )
    else:
        modeladmin.message_user(
            request,
            f"{pushed} pushed, {failed} failed.",
            level=messages.WARNING,
        )


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = (
        "dup_group",
        "retained_bp",
        "retained_account",
        "status",
        "created_at",
        "push_now_button",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "retained_bp",
        "retained_account",
        "dup_group__id_number",
        "dup_group__id_type",
    )
    actions = [push_selected_records]

    readonly_fields = (
        "dup_group",
        "retained_bp",
        "retained_account",
        "payload_pretty",
        "created_at",
        "push_now_button",
    )

    fields = (
        "dup_group",
        "retained_bp",
        "retained_account",
        "status",
        "payload_json",
        "payload_pretty",
        "push_now_button",
        "created_at",
    )

    def payload_pretty(self, obj):
        return format_html(
            "<pre style='white-space: pre-wrap; font-size:13px;'>{}</pre>",
            json.dumps(obj.payload_json or {}, indent=2)
        )
    payload_pretty.short_description = "JSON Preview"

    def push_now_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">Push Now</a>',
                f"/admin/dedupe/pushcleanseddata/{obj.pk}/push/"
            )
        return "-"
    push_now_button.short_description = "Push Individual"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:object_id>/push/",
                self.admin_site.admin_view(self.process_push),
                name="pushcleanseddata-push",
            ),
        ]
        return custom_urls + urls

    def process_push(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)

        try:
            obj.status = "PUSHED"
            obj.save()
            self.message_user(request, "Record pushed successfully.", messages.SUCCESS)
        except Exception as e:
            obj.status = "ERROR"
            obj.save()
            self.message_user(request, f"Push failed: {str(e)}", messages.ERROR)

        return HttpResponseRedirect(f"/admin/dedupe/pushcleanseddata/{obj.pk}/change/")