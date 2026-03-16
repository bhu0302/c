from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import path
from django.http import HttpResponseRedirect
import json

from .models import DupGroup, DupMember, PushCleansedData
from .utils import build_push_json_for_group
import ast


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _read_score_data(obj):
    # 1) Try common JSON/text fields
    possible_fields = [
        "score_breakdown",
        "score_details",
        "score_json",
        "scores",
        "score_components",
        "breakdown",
        "component_scores",
        "score_factors",
    ]

    for field in possible_fields:
        if hasattr(obj, field):
            raw = getattr(obj, field, None)

            if isinstance(raw, dict):
                return raw

            if isinstance(raw, str) and raw.strip():
                try:
                    return json.loads(raw)
                except Exception:
                    try:
                        parsed = ast.literal_eval(raw)
                        if isinstance(parsed, dict):
                            return parsed
                    except Exception:
                        pass

    # 2) Try separate numeric columns directly on model
    data = {
        "active_installation": getattr(obj, "active_installation", 0) or 0,
        "contract_score": getattr(obj, "contract_score", 0) or 0,
        "recent_movein": getattr(obj, "recent_movein", 0) or 0,
        "oldest_bp_bonus": getattr(obj, "oldest_bp_bonus", 0) or 0,
        "profile_completeness": getattr(obj, "profile_completeness", 0) or 0,
        "address_consistency": getattr(obj, "address_consistency", 0) or 0,
        "financial_score": getattr(obj, "financial_score", 0) or 0,
    }

    if any(v != 0 for v in data.values()):
        return data

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

def _push_group_field_name():
    """
    Detect the FK / OneToOne field on PushCleansedData that points to DupGroup.
    Works for names like: dup_group, group, dupgroup, etc.
    """
    preferred_names = ["dup_group", "group", "dupgroup", "dup_group_ref", "dup_group_fk"]

    model_fields = {f.name: f for f in PushCleansedData._meta.get_fields() if hasattr(f, "related_model")}

    for name in preferred_names:
        f = model_fields.get(name)
        if f and getattr(f, "related_model", None) == DupGroup:
            return name

    for f in PushCleansedData._meta.get_fields():
        if getattr(f, "related_model", None) == DupGroup:
            return f.name

    return None


def _push_group_lookup_kwargs(group_obj):
    field_name = _push_group_field_name()
    if not field_name:
        raise ValueError("No FK/OneToOne field found on PushCleansedData pointing to DupGroup.")
    return {field_name: group_obj}


def _get_push_record_for_group(group_obj):
    field_name = _push_group_field_name()
    if not field_name:
        return None
    try:
        return PushCleansedData.objects.filter(**{field_name: group_obj}).first()
    except Exception:
        return None


# ------------------------------------------------------------
# DupMember Inline
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# DupGroup actions
# ------------------------------------------------------------
@admin.action(description="Prepare Push Data for selected groups")
def prepare_push_data(modeladmin, request, queryset):
    prepared = 0
    failed = 0

    for group in queryset:
        try:
            payload = build_push_json_for_group(group)

            lookup = _push_group_lookup_kwargs(group)

            PushCleansedData.objects.update_or_create(
                **lookup,
                defaults={
                    "retained_bp": payload.get("retained_bp"),
                    "retained_account": payload.get("retained_account"),
                    "payload_json": payload,
                    "status": "READY",
                },
            )
            prepared += 1

        except Exception as e:
            failed += 1
            try:
                lookup = _push_group_lookup_kwargs(group)
                PushCleansedData.objects.update_or_create(
                    **lookup,
                    defaults={
                        "retained_bp": None,
                        "retained_account": None,
                        "payload_json": {
                            "dup_group_id": getattr(group, "id", None),
                            "error": str(e),
                        },
                        "status": "ERROR",
                    },
                )
            except Exception:
                pass

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
            lookup = _push_group_lookup_kwargs(group)

            obj, _ = PushCleansedData.objects.update_or_create(
                **lookup,
                defaults={
                    "retained_bp": payload.get("retained_bp"),
                    "retained_account": payload.get("retained_account"),
                    "payload_json": payload,
                    "status": "READY",
                },
            )

            # Placeholder for real push logic
            obj.status = "PUSHED"
            obj.save()
            pushed += 1

        except Exception as e:
            failed += 1
            try:
                lookup = _push_group_lookup_kwargs(group)
                PushCleansedData.objects.update_or_create(
                    **lookup,
                    defaults={
                        "retained_bp": None,
                        "retained_account": None,
                        "payload_json": {
                            "dup_group_id": getattr(group, "id", None),
                            "error": str(e),
                        },
                        "status": "ERROR",
                    },
                )
            except Exception:
                pass

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


# ------------------------------------------------------------
# DupGroup Admin
# ------------------------------------------------------------
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
        push_obj = _get_push_record_for_group(obj)
        if push_obj:
            return format_html(
                '<a href="/admin/dedupe/pushcleanseddata/{}/change/">View Push Data</a>',
                push_obj.pk,
            )
        return "-"

    push_data_link.short_description = "Push Cleansed Data"


# ------------------------------------------------------------
# DupMember Admin
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# PushCleansedData actions
# ------------------------------------------------------------
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
            try:
                obj.status = "ERROR"
                obj.save()
            except Exception:
                pass
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


# ------------------------------------------------------------
# PushCleansedData Admin
# ------------------------------------------------------------
@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = (
        "group_ref",
        "retained_bp",
        "retained_account",
        "status",
        "created_at",
        "push_now_button",
    )

    list_filter = ("status", "created_at")

    actions = [push_selected_records]

    readonly_fields = (
        "group_ref",
        "retained_bp",
        "retained_account",
        "payload_pretty",
        "created_at",
        "push_now_button",
    )

    fields = (
        "group_ref",
        "retained_bp",
        "retained_account",
        "status",
        "payload_json",
        "payload_pretty",
        "push_now_button",
        "created_at",
    )

    def get_search_fields(self, request):
        field_name = _push_group_field_name()
        fields = ["retained_bp", "retained_account"]
        if field_name:
            fields.extend([f"{field_name}__id_number", f"{field_name}__id_type"])
        return fields

    def group_ref(self, obj):
        field_name = _push_group_field_name()
        if field_name and hasattr(obj, field_name):
            return getattr(obj, field_name)
        return "-"

    group_ref.short_description = "Dup Group"

    def payload_pretty(self, obj):
        return format_html(
            "<pre style='white-space: pre-wrap; font-size:13px;'>{}</pre>",
            json.dumps(obj.payload_json or {}, indent=2),
        )

    payload_pretty.short_description = "JSON Preview"

    def push_now_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">Push Now</a>',
                f"/admin/dedupe/pushcleanseddata/{obj.pk}/push/",
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

        if obj is None:
            self.message_user(request, "Record not found.", messages.ERROR)
            return HttpResponseRedirect("/admin/dedupe/pushcleanseddata/")

        try:
            obj.status = "PUSHED"
            obj.save()
            self.message_user(request, "Record pushed successfully.", messages.SUCCESS)
        except Exception as e:
            try:
                obj.status = "ERROR"
                obj.save()
            except Exception:
                pass
            self.message_user(request, f"Push failed: {str(e)}", messages.ERROR)

        return HttpResponseRedirect(f"/admin/dedupe/pushcleanseddata/{obj.pk}/change/")