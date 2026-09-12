import re

from django.shortcuts import render
from ingestion.models import StgCustomerMaster, StgAddress


# ==========================================================
# EMAIL PROFILING
# ==========================================================

def profile_email(email):
    """
    Email completeness and basic validity profiling.
    """

    if email is None:
        return {
            "original": "",
            "normalized": "",
            "status": "MISSING",
            "issue": "MISSING",
        }

    original = str(email).strip()

    if original == "":
        return {
            "original": "",
            "normalized": "",
            "status": "MISSING",
            "issue": "MISSING",
        }

    normalized = original.lower()

    if " " in normalized:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "INVALID_SPACE",
        }

    if normalized.count("@") == 0:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "MISSING_AT",
        }

    if normalized.count("@") > 1:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "MULTIPLE_AT",
        }

    local_part, domain = normalized.split("@")

    if not local_part:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "MISSING_LOCAL_PART",
        }

    if not domain:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "MISSING_DOMAIN",
        }

    if "." not in domain:
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "MISSING_DOMAIN_DOT",
        }

    if domain.startswith(".") or domain.endswith("."):
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "INVALID_DOMAIN",
        }

    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"

    if not re.match(pattern, normalized):
        return {
            "original": original,
            "normalized": normalized,
            "status": "INVALID",
            "issue": "INVALID_FORMAT",
        }

    return {
        "original": original,
        "normalized": normalized,
        "status": "VALID",
        "issue": "",
    }


# ==========================================================
# MOBILE PROFILING
# ==========================================================

def normalize_mobile(mobile, country_key="AE"):
    """
    UAE mobile normalization.

    Supported examples:

    0501234567
    501234567
    971501234567
    +971501234567
    00971501234567

    All normalize to:
    +971501234567
    """

    if mobile is None:
        return {
            "original": "",
            "normalized": "",
            "status": "MISSING",
            "pattern": "MISSING",
            "country_key": country_key,
        }

    original = str(mobile).strip()

    if original == "":
        return {
            "original": "",
            "normalized": "",
            "status": "MISSING",
            "pattern": "MISSING",
            "country_key": country_key,
        }

    cleaned = re.sub(r"[^\d+]", "", original)

    if country_key == "AE":

        if cleaned.startswith("00971"):
            national = cleaned[5:]

            if len(national) == 9 and national.isdigit():
                return {
                    "original": original,
                    "normalized": "+971" + national,
                    "status": "VALID",
                    "pattern": "00_COUNTRY_CODE",
                    "country_key": "AE",
                }

        elif cleaned.startswith("+971"):
            national = cleaned[4:]

            if len(national) == 9 and national.isdigit():
                return {
                    "original": original,
                    "normalized": "+971" + national,
                    "status": "VALID",
                    "pattern": "PLUS_COUNTRY_CODE",
                    "country_key": "AE",
                }

        elif cleaned.startswith("971"):
            national = cleaned[3:]

            if len(national) == 9 and national.isdigit():
                return {
                    "original": original,
                    "normalized": "+971" + national,
                    "status": "VALID",
                    "pattern": "COUNTRY_CODE",
                    "country_key": "AE",
                }

        elif (
            cleaned.startswith("0")
            and len(cleaned) == 10
            and cleaned.isdigit()
        ):
            national = cleaned[1:]

            return {
                "original": original,
                "normalized": "+971" + national,
                "status": "VALID",
                "pattern": "LOCAL_WITH_ZERO",
                "country_key": "AE",
            }

        elif cleaned.isdigit() and len(cleaned) == 9:

            return {
                "original": original,
                "normalized": "+971" + cleaned,
                "status": "VALID",
                "pattern": "LOCAL_WITHOUT_ZERO",
                "country_key": "AE",
            }

        return {
            "original": original,
            "normalized": cleaned,
            "status": "INVALID",
            "pattern": "INVALID_LENGTH_OR_FORMAT",
            "country_key": "AE",
        }

    return {
        "original": original,
        "normalized": cleaned,
        "status": "UNVALIDATED",
        "pattern": "COUNTRY_RULE_NOT_DEFINED",
        "country_key": country_key,
    }


# ==========================================================
# HELPER
# ==========================================================

def safe_text(value):
    """
    Convert database value to trimmed string safely.
    """

    if value is None:
        return ""

    return str(value).strip()


# ==========================================================
# MAIN PROFILING DASHBOARD
# ==========================================================

def profiling_dashboard(request):

    customers = StgCustomerMaster.objects.all()
    addresses = StgAddress.objects.all()

    total = customers.count()
    total_address_records = addresses.count()


    # ======================================================
    # EMAIL COUNTERS
    # ======================================================

    missing_email = 0
    valid_email = 0
    invalid_email = 0

    missing_at = 0
    multiple_at = 0
    missing_local_part = 0
    missing_domain = 0
    missing_domain_dot = 0
    invalid_domain = 0
    invalid_space = 0
    invalid_email_format = 0

    normalized_email_map = {}


    # ======================================================
    # MOBILE COUNTERS
    # ======================================================

    missing_mobile = 0
    valid_mobile = 0
    invalid_mobile = 0
    unvalidated_mobile = 0

    local_with_zero = 0
    local_without_zero = 0
    with_country_code = 0
    with_plus_country_code = 0
    with_00_country_code = 0

    normalized_mobile_map = {}


    # ======================================================
    # PROCESS CUSTOMER MASTER
    # ======================================================

    for customer in customers:

        # ==================================================
        # EMAIL
        # ==================================================

        email_result = profile_email(
            customer.email
        )

        if email_result["status"] == "MISSING":
            missing_email += 1

        elif email_result["status"] == "INVALID":

            invalid_email += 1

            issue = email_result["issue"]

            if issue == "MISSING_AT":
                missing_at += 1

            elif issue == "MULTIPLE_AT":
                multiple_at += 1

            elif issue == "MISSING_LOCAL_PART":
                missing_local_part += 1

            elif issue == "MISSING_DOMAIN":
                missing_domain += 1

            elif issue == "MISSING_DOMAIN_DOT":
                missing_domain_dot += 1

            elif issue == "INVALID_DOMAIN":
                invalid_domain += 1

            elif issue == "INVALID_SPACE":
                invalid_space += 1

            else:
                invalid_email_format += 1

        elif email_result["status"] == "VALID":

            valid_email += 1

            normalized_email = email_result["normalized"]

            if normalized_email not in normalized_email_map:
                normalized_email_map[normalized_email] = []

            normalized_email_map[normalized_email].append({
                "bp_id": customer.bp_id,
                "contract_account": customer.contract_account,
                "original_email": customer.email,
            })


        # ==================================================
        # MOBILE
        # ==================================================

        # Currently defaulting to UAE.
        # Later replace with customer/address country field.
        country_key = "AE"

        mobile_result = normalize_mobile(
            customer.mobile_number,
            country_key
        )

        if mobile_result["status"] == "MISSING":

            missing_mobile += 1

        elif mobile_result["status"] == "INVALID":

            invalid_mobile += 1

        elif mobile_result["status"] == "UNVALIDATED":

            unvalidated_mobile += 1

        elif mobile_result["status"] == "VALID":

            valid_mobile += 1

            pattern = mobile_result["pattern"]

            if pattern == "LOCAL_WITH_ZERO":
                local_with_zero += 1

            elif pattern == "LOCAL_WITHOUT_ZERO":
                local_without_zero += 1

            elif pattern == "COUNTRY_CODE":
                with_country_code += 1

            elif pattern == "PLUS_COUNTRY_CODE":
                with_plus_country_code += 1

            elif pattern == "00_COUNTRY_CODE":
                with_00_country_code += 1

            normalized_mobile = mobile_result["normalized"]

            if normalized_mobile not in normalized_mobile_map:
                normalized_mobile_map[normalized_mobile] = []

            normalized_mobile_map[normalized_mobile].append({
                "bp_id": customer.bp_id,
                "contract_account": customer.contract_account,
                "original_mobile": customer.mobile_number,
            })


    # ======================================================
    # SHARED EMAIL
    # ======================================================

    shared_email_addresses = []
    email_affected_bps = 0

    for email, bp_list in normalized_email_map.items():

        if len(bp_list) > 1:

            shared_email_addresses.append({
                "email": email,
                "bp_count": len(bp_list),
                "bps": bp_list,
            })

            email_affected_bps += len(bp_list)

    shared_email_addresses.sort(
        key=lambda x: x["bp_count"],
        reverse=True
    )

    shared_email_count = len(
        shared_email_addresses
    )


    # ======================================================
    # SHARED MOBILE
    # ======================================================

    shared_mobile_numbers = []
    mobile_affected_bps = 0

    for mobile, bp_list in normalized_mobile_map.items():

        if len(bp_list) > 1:

            shared_mobile_numbers.append({
                "mobile": mobile,
                "bp_count": len(bp_list),
                "bps": bp_list,
            })

            mobile_affected_bps += len(bp_list)

    shared_mobile_numbers.sort(
        key=lambda x: x["bp_count"],
        reverse=True
    )

    shared_mobile_count = len(
        shared_mobile_numbers
    )


    # ======================================================
    # EMAIL PERCENTAGES
    # ======================================================

    email_available = total - missing_email

    email_completeness_percentage = (
        round(
            (email_available / total) * 100,
            2
        )
        if total else 0
    )

    email_valid_percentage = (
        round(
            (valid_email / total) * 100,
            2
        )
        if total else 0
    )

    email_invalid_percentage = (
        round(
            (invalid_email / total) * 100,
            2
        )
        if total else 0
    )

    shared_email_percentage = (
        round(
            (email_affected_bps / total) * 100,
            2
        )
        if total else 0
    )


    # ======================================================
    # MOBILE PERCENTAGES
    # ======================================================

    mobile_available = total - missing_mobile

    mobile_completeness_percentage = (
        round(
            (mobile_available / total) * 100,
            2
        )
        if total else 0
    )

    mobile_valid_percentage = (
        round(
            (valid_mobile / total) * 100,
            2
        )
        if total else 0
    )

    mobile_invalid_percentage = (
        round(
            (invalid_mobile / total) * 100,
            2
        )
        if total else 0
    )

    shared_mobile_percentage = (
        round(
            (mobile_affected_bps / total) * 100,
            2
        )
        if total else 0
    )


    # ======================================================
    # ADDRESS PROFILING
    # ======================================================

    missing_city = 0
    missing_postcode = 0
    missing_country = 0
    missing_street = 0

    complete_address = 0
    incomplete_address = 0


    for address in addresses:

        city = safe_text(
            address.city
        )

        postcode = safe_text(
            address.postal_code
        )

        country = safe_text(
            address.country
        )

        street = safe_text(
            address.street
        )


        # ----------------------------------------------
        # Missing fields
        # ----------------------------------------------

        if not city:
            missing_city += 1

        if not postcode:
            missing_postcode += 1

        if not country:
            missing_country += 1

        if not street:
            missing_street += 1


        # ----------------------------------------------
        # Complete address
        # ----------------------------------------------

        if (
            city
            and postcode
            and country
            and street
        ):
            complete_address += 1

        else:
            incomplete_address += 1


    # ======================================================
    # ADDRESS PERCENTAGES
    # ======================================================

    city_available = (
        total_address_records - missing_city
    )

    postcode_available = (
        total_address_records - missing_postcode
    )

    country_available = (
        total_address_records - missing_country
    )

    street_available = (
        total_address_records - missing_street
    )


    city_completeness_percentage = (
        round(
            (city_available / total_address_records) * 100,
            2
        )
        if total_address_records else 0
    )


    postcode_completeness_percentage = (
        round(
            (postcode_available / total_address_records) * 100,
            2
        )
        if total_address_records else 0
    )


    country_completeness_percentage = (
        round(
            (country_available / total_address_records) * 100,
            2
        )
        if total_address_records else 0
    )


    street_completeness_percentage = (
        round(
            (street_available / total_address_records) * 100,
            2
        )
        if total_address_records else 0
    )


    address_complete_percentage = (
        round(
            (complete_address / total_address_records) * 100,
            2
        )
        if total_address_records else 0
    )


    # ======================================================
    # CONTEXT
    # ======================================================

    context = {

        # ==================================================
        # OVERALL
        # ==================================================

        "total":
            total,


        # ==================================================
        # EMAIL SUMMARY
        # ==================================================

        "email_available":
            email_available,

        "missing_email":
            missing_email,

        "valid_email":
            valid_email,

        "invalid_email":
            invalid_email,

        "email_completeness_percentage":
            email_completeness_percentage,

        "email_valid_percentage":
            email_valid_percentage,

        "email_invalid_percentage":
            email_invalid_percentage,


        # ==================================================
        # EMAIL QUALITY ISSUES
        # ==================================================

        "missing_at":
            missing_at,

        "multiple_at":
            multiple_at,

        "missing_local_part":
            missing_local_part,

        "missing_domain":
            missing_domain,

        "missing_domain_dot":
            missing_domain_dot,

        "invalid_domain":
            invalid_domain,

        "invalid_space":
            invalid_space,

        "invalid_email_format":
            invalid_email_format,


        # ==================================================
        # SHARED EMAIL
        # ==================================================

        "shared_email_count":
            shared_email_count,

        "email_affected_bps":
            email_affected_bps,

        "shared_email_percentage":
            shared_email_percentage,

        "shared_email_addresses":
            shared_email_addresses,


        # ==================================================
        # MOBILE SUMMARY
        # ==================================================

        "mobile_available":
            mobile_available,

        "missing_mobile":
            missing_mobile,

        "valid_mobile":
            valid_mobile,

        "invalid_mobile":
            invalid_mobile,

        "unvalidated_mobile":
            unvalidated_mobile,

        "mobile_completeness_percentage":
            mobile_completeness_percentage,

        "mobile_valid_percentage":
            mobile_valid_percentage,

        "mobile_invalid_percentage":
            mobile_invalid_percentage,


        # ==================================================
        # MOBILE PATTERNS
        # ==================================================

        "local_with_zero":
            local_with_zero,

        "local_without_zero":
            local_without_zero,

        "with_country_code":
            with_country_code,

        "with_plus_country_code":
            with_plus_country_code,

        "with_00_country_code":
            with_00_country_code,


        # ==================================================
        # SHARED MOBILE
        # ==================================================

        "shared_mobile_count":
            shared_mobile_count,

        "mobile_affected_bps":
            mobile_affected_bps,

        "shared_mobile_percentage":
            shared_mobile_percentage,

        "shared_mobile_numbers":
            shared_mobile_numbers,


        # ==================================================
        # ADDRESS SUMMARY
        # ==================================================

        "total_address_records":
            total_address_records,

        "complete_address":
            complete_address,

        "incomplete_address":
            incomplete_address,

        "address_complete_percentage":
            address_complete_percentage,


        # ==================================================
        # ADDRESS FIELD QUALITY
        # ==================================================

        "city_available":
            city_available,

        "missing_city":
            missing_city,

        "city_completeness_percentage":
            city_completeness_percentage,

        "postcode_available":
            postcode_available,

        "missing_postcode":
            missing_postcode,

        "postcode_completeness_percentage":
            postcode_completeness_percentage,

        "country_available":
            country_available,

        "missing_country":
            missing_country,

        "country_completeness_percentage":
            country_completeness_percentage,

        "street_available":
            street_available,

        "missing_street":
            missing_street,

        "street_completeness_percentage":
            street_completeness_percentage,
    }


    return render(
        request,
        "profiling/dashboard.html",
        context
    )