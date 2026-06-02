from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse


def home(request):
    return HttpResponse(
        'Utility Portal is running ✅ <br><a href="/dashboard/">Open Dashboard</a>'
    )


urlpatterns = [
    path("", home, name="home"),

    # Django Admin
    path("admin/", admin.site.urls),

    # App URLs
    path("", include("ingestion.urls")),
    path("", include("dedupe.urls")),
    path("ticket-audit/", include("ticket_audit.urls")),
    # Optional future module
    # path("ticket-audit/", include("ticket_audit.urls")),
]


# Admin Portal Labels
admin.site.site_header = "Utility Data Cleansing Portal"
admin.site.site_title = "Utility Admin"
admin.site.index_title = "Welcome to Bhushan's Utility BP Merge System"