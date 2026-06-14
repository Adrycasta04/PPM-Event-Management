from django.urls import path

from .views import (
    EventCreateView,
    EventDeleteView,
    EventDetailView,
    EventListView,
    EventUpdateView,
    HomeView,
    MyEventListView,
)


app_name = "events"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("events/", EventListView.as_view(), name="list"),
    path("events/mine/", MyEventListView.as_view(), name="my_events"),
    path("events/create/", EventCreateView.as_view(), name="create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="detail"),
    path("events/<int:pk>/edit/", EventUpdateView.as_view(), name="update"),
    path("events/<int:pk>/delete/", EventDeleteView.as_view(), name="delete"),
]
