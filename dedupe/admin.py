from django.contrib import admin
from .models import DupGroup, DupMember, PushCleansedData


def build_push_message(group):
    if not group:
        return ""

    members = DupMember.objects.filter(group_id=group.id)

    retained_bp = ""
    unretained_bps = []
    unretained_installations = []

    for m in members:
        if getattr(m, "is_retained", False):
            retained_bp = str(getattr(m, "bp_number", ""))
        else:
            unretained_bps.append(str(getattr(m, "bp_number", "")))

            inst = getattr(m, "installation", None)
            if inst:
                unretained_installations.append(str(inst))

    lines = []
    if retained_bp:
        lines.append(f"Retained BP: {retained_bp}")
    if unretained_bps:
        lines.append(f"Unretained BPs: {', '.join(unretained_bps)}")
    if unretained_installations:
        lines.append(f"Unretained Installations: {', '.join(unretained_installations)}")

    return "\n".join(lines)


class DupMemberInline(admin.TabularInline):
    model = DupMember
    extra = 0


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    inlines = [DupMemberInline]


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = ("id",)

    def get_fields(self, request, obj=None):
        fields = []
        model_field_names = [f.name for f in self.model._meta.fields]

        if "dup_group" in model_field_names:
            fields.append("dup_group")
        elif "group_id" in model_field_names:
            fields.append("group_id")
        elif "group" in model_field_names:
            fields.append("group")

        if "status" in model_field_names:
            fields.append("status")
        if "push_message" in model_field_names:
            fields.append("push_message")
        if "created_at" in model_field_names:
            fields.append("created_at")

        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly = []
        model_field_names = [f.name for f in self.model._meta.fields]

        if "push_message" in model_field_names:
            readonly.append("push_message")
        if "created_at" in model_field_names:
            readonly.append("created_at")

        return readonly

    def save_model(self, request, obj, form, change):
        group = None

        if hasattr(obj, "dup_group"):
            group = obj.dup_group
        elif hasattr(obj, "group_id"):
            group = obj.group_id
        elif hasattr(obj, "group"):
            group = obj.group

        obj.push_message = build_push_message(group)
        super().save_model(request, obj, form, change)