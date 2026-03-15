import base64
from io import BytesIO
from django.contrib import admin
from .models import DupGroup, DupMember


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "id_type", "id_number", "dup_count", "created_at")


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = ("group", "bp_id", "score_total", "retain_candidate")

    def _make_pie_chart_base64(self, obj):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        members = list(DupMember.objects.filter(group=obj.group).order_by("-score_total"))
        labels = [m.bp_id for m in members]
        scores = [float(m.score_total or 0) for m in members]

        if sum(scores) == 0:
            scores = [1.0 for _ in scores]

        explode = [0.12 if m.retain_candidate else 0.0 for m in members]

        fig = plt.figure(figsize=(6.5, 4.5))
        plt.pie(scores, labels=labels, autopct="%1.1f%%", explode=explode)

        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=160, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)

        return base64.b64encode(buf.read()).decode("utf-8")