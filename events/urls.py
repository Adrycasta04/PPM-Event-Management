from django.urls import path

from .views import EventDetailView, EventListView, HomeView


app_name = "events"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("events/", EventListView.as_view(), name="list"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="detail"),
]
