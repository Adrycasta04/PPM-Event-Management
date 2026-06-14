from django.contrib import admin

from .models import Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organizer",
        "starts_at",
        "location",
        "capacity",
        "status",
    )
    list_filter = ("status", "starts_at")
    search_fields = ("title", "location", "organizer__username")
    list_select_related = ("organizer",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "starts_at"
    ordering = ("starts_at",)
    view_on_site = False


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("attendee", "event", "created_at")
    list_filter = ("created_at", "event")
    search_fields = ("attendee__username", "event__title")
    list_select_related = ("attendee", "event")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
