from django.urls import path
from . import views

urlpatterns = [
    path("", views.ticket_home, name="ticket_home"),
]