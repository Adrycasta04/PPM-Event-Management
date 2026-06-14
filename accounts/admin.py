from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    list_select_related = ("user",)
    readonly_fields = ("created_at", "updated_at")
