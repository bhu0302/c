from django.contrib import admin
from .models import DupGroup, DupMember, PushCleansedData


class DupMemberInline(admin.TabularInline):
    model = DupMember
    extra = 0


@admin.register(DupGroup)
class DupGroupAdmin(admin.ModelAdmin):
    inlines = [DupMemberInline]


@admin.register(DupMember)
class DupMemberAdmin(admin.ModelAdmin):
    list_display = ("id",)


@admin.register(PushCleansedData)
class PushCleansedDataAdmin(admin.ModelAdmin):
    list_display = ("id",)