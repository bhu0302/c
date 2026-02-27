import base64
from io import BytesIO

from django.contrib import admin
from .models import DupGroup, DupMember


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "id_type", "id_number", "dup_count", "created_at")
    search_fields = ("id_type", "id_number")


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = ("group", "bp_id", "score_total", "retain_candidate")
    list_filter = ("retain_candidate",)
    change_form_template = "admin/dedupe/dupmember/change_form.html"

    def _make_pie_chart_base64(self, obj: DupMember) -> str:
        import matplotlib.pyplot as plt

        members = list(
            DupMember.objects.filter(group=obj.group).order_by("-score_total")
        )
        labels = [m.bp_id for m in members]
        scores = [float(m.score_total or 0) for m in members]

        # Avoid matplotlib error if all scores are 0
        if sum(scores) == 0:
            scores = [1.0 for _ in scores]

        explode = [0.12 if m.retain_candidate else 0.0 for m in members]

        fig = plt.figure(figsize=(6.5, 4.5))
        plt.pie(scores, labels=labels, autopct="%1.1f%%", explode=explode)
        plt.title(f"Duplicate Group: {obj.group.id_type}/{obj.group.id_number}")

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=160, bbox_inches="tight")
        plt.close(fig)

        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}

        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                extra_context["dup_pie_chart"] = self._make_pie_chart_base64(obj)
                extra_context["group_members"] = list(
                    DupMember.objects.filter(group=obj.group).order_by("-score_total")
                )

        return super().changeform_view(
            request, object_id, form_url, extra_context=extra_context
        )