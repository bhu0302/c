from django.test import TestCase

# Create your tests here.
from django.urls import path
from . import views
from django.contrib import admin
from dedupe.views import dashboard_view   # adjust if dashboard view is in another app

urlpatterns = [
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/groups/", views.duplicate_groups, name="duplicate_groups"),
    path("dashboard/groups/<int:group_id>/", views.group_detail, name="group_detail"),
    path("admin/", admin.site.urls),
    path("dashboard/", dashboard_view, name="dashboard"),
]
