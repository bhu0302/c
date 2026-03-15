def build_push_json_for_dup_member(dup_member):
    """
    Build JSON payload for target system push.
    Assumptions:
    - dup_member has related duplicate BP records
    - one record is marked retained = True
    - non-retained records may have installation numbers
    """

    all_records = dup_member.records.all()   # change as per your related name
    retained = all_records.filter(is_retained=True).first()

    if not retained:
        return {
            "dup_member_id": dup_member.id,
            "error": "No retained BP found"
        }

    non_retained = all_records.filter(is_retained=False)

    payload = {
        "dup_member_id": dup_member.id,
        "retained_bp": retained.bp_number,
        "retained_account": getattr(retained, "contract_account", None),
        "non_retained_records": []
    }

    for rec in non_retained:
        payload["non_retained_records"].append({
            "bp_id": rec.bp_number,
            "installation": getattr(rec, "installation_number", None),
            "existing_account": getattr(rec, "contract_account", None),
            "target_action": (
                "Create new contract account, create contract, "
                "link non-retained installation, then allow BP merge / financial transfer"
            )
        })

    return payload