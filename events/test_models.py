from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Event, Favorite, Registration, Review


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


class CategoryModelTests(TestCase):
    def test_string_representation_and_ordering(self):
        Category.objects.create(name="Student Associations", slug="associations")
        Category.objects.create(name="Academic Support", slug="academic-support")

        self.assertEqual(
            list(Category.objects.values_list("name", flat=True)),
            [
                "Academic Support",
                "Career",
                "Culture",
                "Music & Nightlife",
                "Other",
                "Social",
                "Sport",
                "Student Associations",
                "Study & Education",
                "Technology",
            ],
        )
        self.assertEqual(
            str(Category.objects.get(slug="associations")),
            "Student Associations",
        )


class FavoriteModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username="favorite-user")
        cls.organizer = get_user_model().objects.create_user(
            username="favorite-organizer"
        )
        starts_at = timezone.now() + timedelta(days=3)
        cls.event = Event.objects.create(
            organizer=cls.organizer,
            title="Favorite model event",
            description="Favorite constraint event.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Campus",
            capacity=20,
            status=Event.Status.PUBLISHED,
        )

    def test_database_prevents_duplicate_favorite(self):
        Favorite.objects.create(event=self.event, user=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Favorite.objects.create(event=self.event, user=self.user)


class ReviewModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(username="review-author")
        cls.other_user = get_user_model().objects.create_user(
            username="review-other"
        )
        cls.organizer = get_user_model().objects.create_user(
            username="review-organizer"
        )
        cls.past_event = Event.objects.create(
            organizer=cls.organizer,
            title="Past review event",
            description="Completed event.",
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(days=2, hours=-2),
            location="Campus",
            capacity=20,
            status=Event.Status.PUBLISHED,
        )
        cls.future_event = Event.objects.create(
            organizer=cls.organizer,
            title="Future review event",
            description="Future event.",
            starts_at=timezone.now() + timedelta(days=2),
            ends_at=timezone.now() + timedelta(days=2, hours=2),
            location="Campus",
            capacity=20,
            status=Event.Status.PUBLISHED,
        )
        Registration.objects.create(event=cls.past_event, attendee=cls.author)
        Registration.objects.create(event=cls.future_event, attendee=cls.author)

    def test_registered_user_can_validate_review_of_past_event(self):
        review = Review(
            event=self.past_event,
            author=self.author,
            rating=5,
            comment="A complete and useful review.",
        )

        review.full_clean()

    def test_review_of_future_event_is_rejected(self):
        review = Review(
            event=self.future_event,
            author=self.author,
            rating=4,
            comment="This event has not happened yet.",
        )

        with self.assertRaises(ValidationError) as error:
            review.full_clean()

        self.assertIn("event", error.exception.message_dict)

    def test_unregistered_user_cannot_review_event(self):
        review = Review(
            event=self.past_event,
            author=self.other_user,
            rating=4,
            comment="I was not registered for this event.",
        )

        with self.assertRaises(ValidationError) as error:
            review.full_clean()

        self.assertIn("author", error.exception.message_dict)

    def test_non_public_event_cannot_be_reviewed(self):
        draft_event = Event.objects.create(
            organizer=self.organizer,
            title="Completed draft event",
            description="A private completed event.",
            starts_at=timezone.now() - timedelta(days=3),
            ends_at=timezone.now() - timedelta(days=3, hours=-2),
            location="Campus",
            capacity=20,
            status=Event.Status.DRAFT,
        )
        Registration.objects.create(event=draft_event, attendee=self.author)
        review = Review(
            event=draft_event,
            author=self.author,
            rating=4,
            comment="A private event cannot receive public reviews.",
        )

        with self.assertRaises(ValidationError) as error:
            review.full_clean()

        self.assertIn("event", error.exception.message_dict)

    def test_database_prevents_duplicate_review(self):
        Review.objects.create(
            event=self.past_event,
            author=self.author,
            rating=5,
            comment="First review for the event.",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    event=self.past_event,
                    author=self.author,
                    rating=4,
                    comment="Duplicate review for the event.",
                )

    def test_database_rejects_rating_outside_range(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    event=self.past_event,
                    author=self.author,
                    rating=6,
                    comment="Invalid rating.",
                )
