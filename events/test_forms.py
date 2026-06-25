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

    def test_datetime_and_status_help_texts_are_clear(self):
        form = EventForm()

        self.assertIn("data sia l'orario", form.fields["starts_at"].help_text)
        self.assertIn("data sia l'orario", form.fields["ends_at"].help_text)
        self.assertIn("Draft = bozza non pubblica", form.fields["status"].help_text)
        self.assertIn("Published = visibile", form.fields["status"].help_text)
        self.assertIn("Cancelled = annullato", form.fields["status"].help_text)

    def test_title_cannot_be_only_spaces(self):
        form = EventForm(data=self.valid_data(title="     "))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_title_must_have_at_least_five_characters(self):
        form = EventForm(data=self.valid_data(title="Abcd"))

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_title_is_stripped_before_save(self):
        form = EventForm(data=self.valid_data(title="  Valid title  "))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["title"], "Valid title")

    def test_location_cannot_be_only_spaces(self):
        form = EventForm(data=self.valid_data(location="     "))

        self.assertFalse(form.is_valid())
        self.assertIn("location", form.errors)

    def test_location_must_have_at_least_three_characters(self):
        form = EventForm(data=self.valid_data(location="AB"))

        self.assertFalse(form.is_valid())
        self.assertIn("location", form.errors)

    def test_location_is_stripped_before_save(self):
        form = EventForm(data=self.valid_data(location="  Florence  "))

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["location"], "Florence")

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
