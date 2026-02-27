from django.urls import path
from . import views

urlpatterns = [
  path("groups/", views.dup_groups, name="dup_groups"),
  path("groups/<int:group_id>/", views.dup_group_detail, name="dup_group_detail"),
]