from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from ingestion.models import StgCustomerMaster
from .models import DupGroup, DupMember


def dashboard_home(request):
    total_bps = StgCustomerMaster.objects.values("bp_id").distinct().count()
    dup_group_count = DupGroup.objects.count()
    duplicate_bps = DupMember.objects.values("bp_id").distinct().count()
    unique_bps = max(total_bps - duplicate_bps, 0)

    ctx = {
        "total_bps": total_bps,
        "duplicate_bps": duplicate_bps,
        "unique_bps": unique_bps,
        "dup_group_count": dup_group_count,
    }
    return render(request, "dedupe/dashboard_home.html", ctx)


def duplicate_groups(request):
    q = (request.GET.get("q") or "").strip()

    qs = DupGroup.objects.all().order_by("-created_at", "-id")
    if q:
        qs = qs.filter(id_number__icontains=q) | qs.filter(id_type__icontains=q)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dedupe/duplicate_groups.html", {
        "page_obj": page_obj,
        "q": q,
    })


def _format_reasons(reasons: dict) -> list[tuple[str, str]]:
    """Return list of (key, value) pairs nicely formatted for template."""
    if not reasons:
        return []
    out = []
    for k, v in reasons.items():
        out.append((str(k).replace("_", " ").title(), str(v)))
    return out


def group_detail(request, group_id: int):
    group = get_object_or_404(DupGroup, id=group_id)
    members = list(DupMember.objects.filter(group=group).order_by("-score_total"))

    retained = next((m for m in members if m.retain_candidate), None)

    labels = [m.bp_id for m in members]
    values = [float(m.score_total or 0) for m in members]
    retained_index = labels.index(retained.bp_id) if retained else -1

    # ✅ add formatted reasons for display
    for m in members:
        m.reasons_pretty = _format_reasons(m.reasons_json or {})

    return render(request, "dedupe/group_detail.html", {
        "group": group,
        "members": members,
        "retained": retained,
        "labels": labels,
        "values": values,
        "retained_index": retained_index,
    })

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def dashboard_view(request):
    context = {
        # your existing dashboard context here
    }
    return render(request, "dashboard.html", context)