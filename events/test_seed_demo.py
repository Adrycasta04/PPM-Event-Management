from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import Profile
from accounts.roles import Role

from .management.commands.seed_demo import DEMO_USERS
from .models import Category, Event, Favorite, Registration, Review


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_creates_complete_idempotent_dataset(self):
        output = StringIO()

        call_command("seed_demo", stdout=output)
        call_command("seed_demo", stdout=output)

        user_model = get_user_model()
        self.assertEqual(
            set(
                user_model.objects.filter(
                    username__in=DEMO_USERS,
                ).values_list("username", flat=True)
            ),
            set(DEMO_USERS),
        )
        self.assertEqual(Profile.objects.filter(user__username__in=DEMO_USERS).count(), 5)
        self.assertEqual(Event.objects.count(), 14)
        self.assertEqual(
            Event.objects.filter(status=Event.Status.PUBLISHED).count(),
            11,
        )
        self.assertEqual(Event.objects.filter(status=Event.Status.DRAFT).count(), 1)
        self.assertEqual(
            Event.objects.filter(status=Event.Status.CANCELLED).count(),
            2,
        )
        self.assertEqual(Category.objects.count(), 8)
        self.assertEqual(Registration.objects.count(), 10)
        self.assertEqual(Favorite.objects.count(), 4)
        self.assertEqual(Review.objects.count(), 3)
        self.assertFalse(Event.objects.filter(category__isnull=True).exists())
        self.assertEqual(
            set(Group.objects.values_list("name", flat=True)),
            {Role.ATTENDEE.value, Role.ORGANIZER.value},
        )

        for username, data in DEMO_USERS.items():
            user = user_model.objects.get(username=username)
            self.assertTrue(user.check_password(data["password"]))

    def test_seed_demo_contains_required_event_scenarios(self):
        call_command("seed_demo", verbosity=0)

        self.assertTrue(
            Event.objects.filter(status=Event.Status.PUBLISHED).exists()
        )
        self.assertTrue(Event.objects.filter(status=Event.Status.DRAFT).exists())
        self.assertTrue(
            Event.objects.filter(status=Event.Status.CANCELLED).exists()
        )

        full_event = Event.objects.get(title="CV and LinkedIn Lab")
        empty_event = Event.objects.get(
            title="Erasmus Welcome Aperitivo"
        )
        available_event = Event.objects.get(
            title="Django Workshop for Beginners"
        )
        organizer_demo_events = Event.objects.filter(
            organizer__username="organizer_demo",
        )
        organizer2_demo_events = Event.objects.filter(
            organizer__username="organizer2_demo",
        )
        student_events = Event.objects.filter(
            description__icontains="student",
        )
        university_events = Event.objects.filter(
            description__icontains="university",
        )

        self.assertEqual(full_event.registrations.count(), full_event.capacity)
        self.assertEqual(empty_event.registrations.count(), 0)
        self.assertLess(
            available_event.registrations.count(),
            available_event.capacity,
        )
        self.assertGreaterEqual(organizer_demo_events.count(), 6)
        self.assertGreaterEqual(organizer2_demo_events.count(), 5)
        self.assertTrue(
            Registration.objects.filter(
                event__title="Hackathon: Build for Campus",
                attendee__username="organizer_demo",
            ).exists()
        )
        self.assertGreaterEqual(student_events.count(), 5)
        self.assertGreaterEqual(university_events.count(), 3)
        self.assertEqual(
            Event.objects.filter(
                status=Event.Status.PUBLISHED,
                ends_at__lt=timezone.now(),
            ).count(),
            2,
        )
        self.assertFalse(
            Review.objects.filter(event__ends_at__gte=timezone.now()).exists()
        )
        for review in Review.objects.select_related("event", "author"):
            self.assertTrue(
                Registration.objects.filter(
                    event=review.event,
                    attendee=review.author,
                ).exists()
            )

    def test_reset_removes_existing_application_data(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="temporary-user")

        call_command("seed_demo", reset=True, verbosity=0)

        self.assertFalse(
            user_model.objects.filter(username="temporary-user").exists()
        )
        self.assertEqual(user_model.objects.count(), len(DEMO_USERS))

    def test_seed_without_reset_preserves_unrelated_data(self):
        user_model = get_user_model()
        external_user = user_model.objects.create_user(
            username="unrelated-organizer"
        )
        starts_at = timezone.now() + timedelta(days=60)
        external_event = Event.objects.create(
            organizer=external_user,
            title="Unrelated event",
            description="This record is not managed by the demo seed.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="External location",
            capacity=10,
            status=Event.Status.DRAFT,
        )

        call_command("seed_demo", verbosity=0)

        self.assertTrue(
            user_model.objects.filter(pk=external_user.pk).exists()
        )
        self.assertTrue(Event.objects.filter(pk=external_event.pk).exists())
