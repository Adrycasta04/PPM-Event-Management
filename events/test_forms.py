from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .forms import EventForm
from .models import Event


class EventFormTests(TestCase):
    def valid_data(self, **overrides):
        starts_at = timezone.localtime(
            timezone.now() + timedelta(days=7)
        )
        data = {
            "title": "Form event",
            "description": "A valid event created through the form.",
            "starts_at": starts_at.strftime("%Y-%m-%dT%H:%M"),
            "ends_at": (starts_at + timedelta(hours=2)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "location": "Florence",
            "capacity": 25,
            "status": Event.Status.PUBLISHED,
        }
        data.update(overrides)
        return data

    def test_form_exposes_only_explicit_editable_fields(self):
        form = EventForm()

        self.assertEqual(
            list(form.fields),
            [
                "title",
                "description",
                "starts_at",
                "ends_at",
                "location",
                "capacity",
                "status",
            ],
        )
        self.assertNotIn("organizer", form.fields)

    def test_valid_event_data_is_accepted(self):
        form = EventForm(data=self.valid_data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_end_must_be_after_start(self):
        starts_at = timezone.localtime(
            timezone.now() + timedelta(days=7)
        ).strftime("%Y-%m-%dT%H:%M")
        form = EventForm(
            data=self.valid_data(
                starts_at=starts_at,
                ends_at=starts_at,
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("ends_at", form.errors)

    def test_capacity_must_be_at_least_one(self):
        form = EventForm(data=self.valid_data(capacity=0))

        self.assertFalse(form.is_valid())
        self.assertIn("capacity", form.errors)

    def test_status_must_be_a_defined_choice(self):
        form = EventForm(data=self.valid_data(status="unsupported"))

        self.assertFalse(form.is_valid())
        self.assertIn("status", form.errors)
