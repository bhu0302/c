from django.contrib import admin
from django.urls import path, include


admin.site.site_header = "Utility Data Cleansing Portal"
admin.site.site_title = "Utility Admin"
admin.site.index_title = "Welcome to Bhushan's Utility BP Merge System"

urlpatterns = [
    path("admin/", admin.site.urls),

    # include app URLs
    path("", include("ingestion.urls")),
    path("", include("portal.urls")),   # keep only if you created portal app
]
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse('Utility Portal is running ✅ <br><a href="/dashboard/">Open Dashboard</a>')

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("", include("ingestion.urls")),
    path("", include("dedupe.urls")),   # ✅ add this
]