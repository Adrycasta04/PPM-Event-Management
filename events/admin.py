from django.contrib import admin

from .models import Category, Event, Favorite, Registration, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "organizer",
        "starts_at",
        "location",
        "capacity",
        "status",
    )
    list_filter = ("status", "category", "starts_at")
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


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created_at")
    search_fields = ("user__username", "event__title")
    list_select_related = ("user", "event")
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author", "event", "rating", "updated_at")
    list_filter = ("rating", "updated_at")
    search_fields = ("author__username", "event__title", "comment")
    list_select_related = ("author", "event")
    readonly_fields = ("created_at", "updated_at")
