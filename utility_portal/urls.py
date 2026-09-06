from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


# -------------------------------------------------
# Home Page
# -------------------------------------------------
def home(request):
    return HttpResponse(
        'Utility Portal is running ✅'
        '<br><br>'
        '<a href="/dashboard/">Open Dashboard</a>'
        '<br>'
        '<a href="/admin/">Open Admin Portal</a>'
    )


# -------------------------------------------------
# Admin Branding
# -------------------------------------------------
admin.site.site_header = "Utility Data Cleansing Portal"
admin.site.site_title = "Utility Admin"
admin.site.index_title = "Welcome to Bhushan's Utility BP Merge System"


# -------------------------------------------------
# URL Configuration
# -------------------------------------------------
urlpatterns = [

    # Home
    path("", home, name="home"),

    # Django Admin
    path("admin/", admin.site.urls),

    # Data Ingestion
    path("", include("ingestion.urls")),

    # BP Duplicate Detection / Cleansing
    path("", include("dedupe.urls")),

]