from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse("events:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/home.html")


class PublicEventViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="organizer",
        )
        starts_at = timezone.now() + timedelta(days=7)
        common_fields = {
            "organizer": cls.organizer,
            "description": "Event description",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Florence",
            "capacity": 50,
        }
        cls.published_event = Event.objects.create(
            title="Published event",
            status=Event.Status.PUBLISHED,
            **common_fields,
        )
        cls.draft_event = Event.objects.create(
            title="Draft event",
            status=Event.Status.DRAFT,
            **common_fields,
        )
        cls.cancelled_event = Event.objects.create(
            title="Cancelled event",
            status=Event.Status.CANCELLED,
            **common_fields,
        )

    def test_event_list_shows_only_published_events(self):
        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_list.html")
        self.assertQuerySetEqual(
            response.context["events"],
            [self.published_event],
        )
        self.assertContains(response, self.published_event.title)
        self.assertNotContains(response, self.draft_event.title)
        self.assertNotContains(response, self.cancelled_event.title)

    def test_published_event_detail_is_public(self):
        response = self.client.get(self.published_event.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_detail.html")
        self.assertEqual(response.context["event"], self.published_event)

    def test_non_public_event_details_return_not_found(self):
        for event in (self.draft_event, self.cancelled_event):
            with self.subTest(status=event.status):
                response = self.client.get(event.get_absolute_url())
                self.assertEqual(response.status_code, 404)


class EmptyEventListTests(TestCase):
    def test_event_list_has_empty_state(self):
        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Non ci sono eventi pubblicati")
