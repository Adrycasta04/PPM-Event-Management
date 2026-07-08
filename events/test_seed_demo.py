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
from .models import Event, Registration


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
        self.assertEqual(Event.objects.count(), 9)
        self.assertEqual(Registration.objects.count(), 7)
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

        full_event = Event.objects.get(title="Urban Photography Workshop")
        empty_event = Event.objects.get(
            title="Multimedia Production Open Day"
        )
        available_event = Event.objects.get(
            title="Django Community Meetup Florence"
        )

        self.assertEqual(full_event.registrations.count(), full_event.capacity)
        self.assertEqual(empty_event.registrations.count(), 0)
        self.assertLess(
            available_event.registrations.count(),
            available_event.capacity,
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
