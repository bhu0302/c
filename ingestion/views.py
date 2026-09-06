import csv
import io

from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render, redirect

from .forms import UploadCSVForm
from .models import (
    StgCustomerMaster,
    StgFinancial,
    StgAddress,
)


def _parse_date(value):
    value = (value or "").strip()

    if not value:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


# ============================================================
# CUSTOMER MASTER UPLOAD
# ============================================================

def upload_customer_master(request):

    if request.method == "POST":

        form = UploadCSVForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            f = request.FILES["file"]

            data = io.StringIO(
                f.read().decode("utf-8-sig")
            )

            reader = csv.DictReader(data)

            rows = []

            for r in reader:

                rows.append(
                    StgCustomerMaster(

                        bp_id=(
                            r.get("bp_id") or ""
                        ).strip(),

                        bp_number=(
                            r.get("bp_number") or ""
                        ).strip(),

                        bp_creation_date=_parse_date(
                            r.get("bp_creation_date")
                        ),

                        bp_creation_source=(
                            r.get("bp_creation_source") or ""
                        ).strip(),

                        id_type=(
                            r.get("id_type") or ""
                        ).strip(),

                        id_number=(
                            r.get("id_number") or ""
                        ).strip(),

                        email=(
                            r.get("email") or ""
                        ).strip(),

                        mobile_number=(
                            r.get("mobile_number") or ""
                        ).strip(),

                        date_of_birth=_parse_date(
                            r.get("date_of_birth")
                        ),

                        nationality=(
                            r.get("nationality") or ""
                        ).strip(),

                        gender=(
                            r.get("gender") or ""
                        ).strip(),

                        contract_account=(
                            r.get("contract_account") or ""
                        ).strip(),

                        contract=(
                            r.get("contract") or ""
                        ).strip(),

                        installation=(
                            r.get("installation") or ""
                        ).strip(),

                        move_in_date=_parse_date(
                            r.get("move_in_date")
                        ),

                        move_out_date=_parse_date(
                            r.get("move_out_date")
                        ),
                    )
                )

            # APPEND - does NOT delete existing records
            StgCustomerMaster.objects.bulk_create(
                rows,
                batch_size=1000
            )

            return redirect("upload_success")

    else:
        form = UploadCSVForm()

    return render(
        request,
        "ingestion/upload.html",
        {
            "form": form,
            "title": "Upload Customer Master CSV"
        }
    )


# ============================================================
# FINANCIAL UPLOAD
# ============================================================

def upload_financial(request):

    if request.method == "POST":

        form = UploadCSVForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            f = request.FILES["file"]

            data = io.StringIO(
                f.read().decode("utf-8-sig")
            )

            reader = csv.DictReader(data)

            rows = []

            for r in reader:

                rows.append(
                    StgFinancial(

                        bp_id=(
                            r.get("bp_id") or ""
                        ).strip(),

                        contract_account=(
                            r.get("contract_account") or ""
                        ).strip(),

                        payment_date=_parse_date(
                            r.get("payment_date")
                        ),

                        payment_amount=(
                            r.get("payment_amount") or "0"
                        ).strip() or "0",
                    )
                )

            # APPEND
            StgFinancial.objects.bulk_create(
                rows,
                batch_size=2000
            )

            return redirect("upload_success")

    else:
        form = UploadCSVForm()

    return render(
        request,
        "ingestion/upload.html",
        {
            "form": form,
            "title": "Upload Financial CSV"
        }
    )


# ============================================================
# ADDRESS UPLOAD
# ============================================================

def upload_address(request):

    if request.method == "POST":

        form = UploadCSVForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            f = request.FILES["file"]

            data = io.StringIO(
                f.read().decode("utf-8-sig")
            )

            reader = csv.DictReader(data)

            rows = []

            for r in reader:

                rows.append(
                    StgAddress(

                        bp_id=(
                            r.get("bp_id") or ""
                        ).strip(),

                        addr_line1=(
                            r.get("addr_line1") or ""
                        ).strip(),

                        addr_line2=(
                            r.get("addr_line2") or ""
                        ).strip(),

                        building=(
                            r.get("building") or ""
                        ).strip(),

                        flat=(
                            r.get("flat") or ""
                        ).strip(),

                        street=(
                            r.get("street") or ""
                        ).strip(),

                        area=(
                            r.get("area") or ""
                        ).strip(),

                        city=(
                            r.get("city") or ""
                        ).strip(),

                        postal_code=(
                            r.get("postal_code") or ""
                        ).strip(),

                        country=(
                            r.get("country") or ""
                        ).strip(),
                    )
                )

            # APPEND
            StgAddress.objects.bulk_create(
                rows,
                batch_size=2000
            )

            return redirect("upload_success")

    else:
        form = UploadCSVForm()
git push origin main
    return render(
        request,
        "ingestion/upload.html",
        {
            "form": form,
            "title": "Upload Address CSV"
        }
    )


# ============================================================
# SUCCESS PAGE
# ============================================================

def upload_success(request):

    return HttpResponse(
        """
        <h2>✅ Upload successful</h2>

        <p>
            <a href="/">Return to Home</a>
        </p>

        <p>
            <a href="/admin/">Open Admin</a>
        </p>

        <p>
            <a href="/dashboard/">Open Dashboard</a>
        </p>
        """
    )