from django.urls import path
from . import views

urlpatterns = [
    path("upload/customer/", views.upload_customer_master, name="upload_customer"),
    path("upload/financial/", views.upload_financial, name="upload_financial"),
    path("upload/address/", views.upload_address, name="upload_address"),
    path("upload/success/", views.upload_success, name="upload_success"),
]
