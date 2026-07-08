from django.urls import path

from .views import (
    EventAttendeeListView,
    EventCreateView,
    EventDeleteView,
    EventDetailView,
    EventListView,
    EventRegistrationCreateView,
    EventRegistrationDeleteView,
    EventUpdateView,
    ContactView,
    HomeView,
    MyEventListView,
    MyRegistrationListView,
)


app_name = "events"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("contact/", ContactView.as_view(), name="contact"),
    path("events/", EventListView.as_view(), name="list"),
    path("events/mine/", MyEventListView.as_view(), name="my_events"),
    path(
        "registrations/mine/",
        MyRegistrationListView.as_view(),
        name="my_registrations",
    ),
    path("events/create/", EventCreateView.as_view(), name="create"),
    path("events/<int:pk>/", EventDetailView.as_view(), name="detail"),
    path(
        "events/<int:pk>/attendees/",
        EventAttendeeListView.as_view(),
        name="attendees",
    ),
    path(
        "events/<int:pk>/register/",
        EventRegistrationCreateView.as_view(),
        name="register",
    ),
    path("events/<int:pk>/edit/", EventUpdateView.as_view(), name="update"),
    path("events/<int:pk>/delete/", EventDeleteView.as_view(), name="delete"),
    path(
        "registrations/<int:pk>/cancel/",
        EventRegistrationDeleteView.as_view(),
        name="cancel_registration",
    ),
]
