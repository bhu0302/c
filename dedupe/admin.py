from django.contrib import admin
from .models import DupGroup, DupMember, PushCleansedData


def build_push_message(group):
    if not group:
        return ""

    # change "group_id" below later only if your FK field name is different
    members = DupMember.objects.filter(group_id=group)

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
    readonly_fields = ("push_message", "created_at")

    def get_fields(self, request, obj=None):
        fields = []

        # show the group selector only if this field exists in model
        model_field_names = [f.name for f in self.model._meta.fields]

        if "dup_group" in model_field_names:
            fields.append("dup_group")
        elif "group_id" in model_field_names:
            fields.append("group_id")
        elif "group" in model_field_names:
            fields.append("group")

        if "push_message" in model_field_names:
            fields.append("push_message")
        if "created_at" in model_field_names:
            fields.append("created_at")

        return fields

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