from django.urls import path
from . import views

app_name = "profiling"

urlpatterns = [
    path("", views.profiling_dashboard, name="dashboard"),
    path("email/", views.email_quality, name="email_quality"),
    path("mobile/", views.mobile_quality, name="mobile_quality"),
    path("address/", views.address_quality, name="address_quality"),
    path("shared-email/", views.shared_email_detail, name="shared_email"),
    path("shared-mobile/", views.shared_mobile_detail, name="shared_mobile"),

]