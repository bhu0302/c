from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from dedupe.models import DupGroup, DupMember

def dup_groups(request):
    groups = DupGroup.objects.order_by("-created_at")
    return render(request, "portal/groups.html", {"groups": groups})

def dup_group_detail(request, group_id):
    group = get_object_or_404(DupGroup, id=group_id)
    members = DupMember.objects.filter(group=group).order_by("-retain_candidate","-score_total")
    return render(request, "portal/group_detail.html", {"group": group, "members": members})