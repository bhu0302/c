from .models import DupMember


def build_push_json_for_group(dup_group):
    members = DupMember.objects.filter(group=dup_group).order_by("-retain_candidate", "-score_total")

    retained = members.filter(retain_candidate=True).first()
    if not retained:
        retained = members.first()

    if not retained:
        return {
            "dup_group_id": dup_group.id,
            "error": "No members found"
        }

    non_retained = members.exclude(id=retained.id)

    payload = {
        "dup_group_id": dup_group.id,
        "id_type": dup_group.id_type,
        "id_number": dup_group.id_number,
        "retained_bp": retained.bp_id,
        "non_retained_entities": []
    }

    for m in non_retained:
        payload["non_retained_entities"].append({
            "bp_id": m.bp_id,
            "installation": getattr(m, "installation_no", None),
            "target_action": "CREATE_CA_CONTRACT_AND_RELINK"
        })

    return payload