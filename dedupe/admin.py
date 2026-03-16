from django.contrib import admin
from .models import DupGroup, DupMember, PushCleansedData


# 👉 ADD THIS FUNCTION HERE
def build_push_message(group):
    if not group:
        return ""

    members = DupMember.objects.filter(group_id=group)

    retained_bp = ""
    unretained_bps = []
    unretained_installations = []

    for m in members:
        if m.is_retained:
            retained_bp = str(m.bp_number)
        else:
            unretained_bps.append(str(m.bp_number))

            if getattr(m, "installation", None):
                unretained_installations.append(str(m.installation))

    message = (
        f"Retained BP: {retained_bp}\n"
        f"Unretained BPs: {', '.join(unretained_bps)}\n"
        f"Unretained Installations: {', '.join(unretained_installations)}"
    )

    return message


# EXISTING ADMIN CLASSES BELOW


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

    list_display = ("id", "created_at")
    readonly_fields = ("push_message", "created_at")

    def save_model(self, request, obj, form, change):

        # 👉 AUTO GENERATE MESSAGE HERE
        obj.push_message = build_push_message(obj.dup_group)

        super().save_model(request, obj, form, change)