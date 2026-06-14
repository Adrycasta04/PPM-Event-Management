from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, Registration


class EventModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="model-organizer",
        )

    def event_fields(self, **overrides):
        starts_at = timezone.now() + timedelta(days=5)
        fields = {
            "organizer": self.organizer,
            "title": "Model event",
            "description": "Model validation event.",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Florence",
            "capacity": 10,
            "status": Event.Status.DRAFT,
        }
        fields.update(overrides)
        return fields

    def test_string_and_absolute_url(self):
        event = Event.objects.create(**self.event_fields())

        self.assertEqual(str(event), "Model event")
        self.assertEqual(
            event.get_absolute_url(),
            reverse("events:detail", args=[event.pk]),
        )

    def test_public_queryset_returns_only_published_events(self):
        draft = Event.objects.create(**self.event_fields(title="Draft"))
        published = Event.objects.create(
            **self.event_fields(
                title="Published",
                status=Event.Status.PUBLISHED,
            )
        )
        cancelled = Event.objects.create(
            **self.event_fields(
                title="Cancelled",
                status=Event.Status.CANCELLED,
            )
        )

        self.assertQuerySetEqual(Event.objects.public(), [published])
        self.assertFalse(draft.is_public)
        self.assertTrue(published.is_public)
        self.assertFalse(cancelled.is_public)

    def test_model_validation_rejects_end_not_after_start(self):
        starts_at = timezone.now() + timedelta(days=5)
        event = Event(
            **self.event_fields(
                starts_at=starts_at,
                ends_at=starts_at,
            )
        )

        with self.assertRaises(ValidationError) as error:
            event.full_clean()

        self.assertIn("ends_at", error.exception.message_dict)

    def test_database_rejects_capacity_below_one(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Event.objects.create(**self.event_fields(capacity=0))

    def test_database_rejects_end_not_after_start(self):
        starts_at = timezone.now() + timedelta(days=5)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Event.objects.create(
                    **self.event_fields(
                        starts_at=starts_at,
                        ends_at=starts_at,
                    )
                )


class RegistrationModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="registration-model-organizer",
        )
        cls.attendee = get_user_model().objects.create_user(
            username="registration-model-attendee",
        )
        starts_at = timezone.now() + timedelta(days=5)
        cls.event = Event.objects.create(
            organizer=cls.organizer,
            title="Registration model event",
            description="Registration constraint event.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Florence",
            capacity=10,
            status=Event.Status.PUBLISHED,
        )

    def test_string_representation(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
        )

        self.assertEqual(
            str(registration),
            "registration-model-attendee - Registration model event",
        )

    def test_database_prevents_duplicate_registration(self):
        Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Registration.objects.create(
                    event=self.event,
                    attendee=self.attendee,
                )

    def test_deleting_event_cascades_to_registrations(self):
        Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
        )

        self.event.delete()

        self.assertFalse(Registration.objects.exists())
