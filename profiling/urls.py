from django.urls import path
from . import views

app_name = "profiling"

urlpatterns = [
    path("", views.profiling_dashboard, name="dashboard"),
]