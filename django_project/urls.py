"""Root URL configuration for the event management project."""

from django.contrib import admin
from django.conf import settings
from django.urls import include, path, re_path
from django.views.static import serve


def serve_media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("events.urls")),
    # The project is a small SQLite demo, so bundled media is served by Django.
    # Runtime uploads on Render remain ephemeral and are documented as such.
    re_path(
        r"^media/(?P<path>.*)$",
        serve_media,
    ),
]
