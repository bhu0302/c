from django.shortcuts import render

# Create your views here.
import csv, io
from django.shortcuts import render, redirect
from .forms import UploadCSVForm
from .models import StgCustomerMaster, StgFinancial, StgAddress

def upload_customer_master(request):
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES["file"]
            data = io.StringIO(f.read().decode("utf-8"))
            reader = csv.DictReader(data)

            StgCustomerMaster.objects.all().delete()  # optional for MVP
            rows = []
            for r in reader:
                rows.append(StgCustomerMaster(
                    bp_id=r.get("bp_id","").strip(),
                    id_type=r.get("id_type"),
                    id_number=r.get("id_number"),
                    email=r.get("email"),
                    mobile_number=r.get("mobile_number"),
                    # parse dates later if needed
                    contract_account=r.get("contract_account"),
                    installation=r.get("installation"),
                ))
            StgCustomerMaster.objects.bulk_create(rows, batch_size=1000)
            return redirect("upload_success")
    else:
        form = UploadCSVForm()
    return render(request, "ingestion/upload.html", {"form": form})


import csv, io
from datetime import datetime
from django.shortcuts import render, redirect
from .forms import UploadCSVForm
from .models import StgCustomerMaster, StgFinancial, StgAddress

def _parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    # expects YYYY-MM-DD
    return datetime.strptime(s, "%Y-%m-%d").date()


def upload_financial(request):
    """
    Expected CSV headers:
    bp_id, contract_account, payment_date, payment_amount
    """
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES["file"]
            data = io.StringIO(f.read().decode("utf-8"))
            reader = csv.DictReader(data)

            # MVP: clear table before load (remove if you want append)
            StgFinancial.objects.all().delete()

            rows = []
            for r in reader:
                rows.append(StgFinancial(
                    bp_id=(r.get("bp_id") or "").strip(),
                    contract_account=(r.get("contract_account") or "").strip(),
                    payment_date=_parse_date(r.get("payment_date")),
                    payment_amount=(r.get("payment_amount") or "0").strip() or "0",
                ))

            StgFinancial.objects.bulk_create(rows, batch_size=2000)
            return redirect("upload_success")
    else:
        form = UploadCSVForm()

    return render(request, "ingestion/upload.html", {
        "form": form,
        "title": "Upload Financial CSV"
    })


def upload_address(request):
    """
    Expected CSV headers:
    bp_id, addr_line1, addr_line2, building, flat, street, area, city, postal_code, country
    """
    if request.method == "POST":
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES["file"]
            data = io.StringIO(f.read().decode("utf-8"))
            reader = csv.DictReader(data)

            # MVP: clear table before load (remove if you want append)
            StgAddress.objects.all().delete()

            rows = []
            for r in reader:
                rows.append(StgAddress(
                    bp_id=(r.get("bp_id") or "").strip(),
                    addr_line1=(r.get("addr_line1") or "").strip(),
                    addr_line2=(r.get("addr_line2") or "").strip(),
                    building=(r.get("building") or "").strip(),
                    flat=(r.get("flat") or "").strip(),
                    street=(r.get("street") or "").strip(),
                    area=(r.get("area") or "").strip(),
                    city=(r.get("city") or "").strip(),
                    postal_code=(r.get("postal_code") or "").strip(),
                    country=(r.get("country") or "").strip(),
                ))

            StgAddress.objects.bulk_create(rows, batch_size=2000)
            return redirect("upload_success")
    else:
        form = UploadCSVForm()

    return render(request, "ingestion/upload.html", {
        "form": form,
        "title": "Upload Address CSV"
    })
from django.http import HttpResponse

def upload_success(request):
    return HttpResponse("✅ Upload successful")