from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from accounts.roles import Role
from events.models import Event, Registration


DEMO_USERS = {
    "admin_demo": {
        "password": "admin12345",
        "first_name": "Demo",
        "last_name": "Admin",
        "email": "admin@example.test",
        "is_staff": True,
        "is_superuser": True,
        "role": None,
        "bio": "Demo administrator account.",
    },
    "attendee_demo": {
        "password": "attendee12345",
        "first_name": "Alice",
        "last_name": "Bianchi",
        "email": "alice@example.test",
        "is_staff": False,
        "is_superuser": False,
        "role": Role.ATTENDEE,
        "bio": "Attendee interested in technology and multimedia.",
    },
    "attendee2_demo": {
        "password": "attendee212345",
        "first_name": "Marco",
        "last_name": "Verdi",
        "email": "marco@example.test",
        "is_staff": False,
        "is_superuser": False,
        "role": Role.ATTENDEE,
        "bio": "Attendee interested in photography and podcasting.",
    },
    "organizer_demo": {
        "password": "organizer12345",
        "first_name": "Giulia",
        "last_name": "Rossi",
        "email": "giulia@example.test",
        "is_staff": False,
        "is_superuser": False,
        "role": Role.ORGANIZER,
        "bio": "Organizer of cultural and educational events.",
    },
    "organizer2_demo": {
        "password": "organizer212345",
        "first_name": "Luca",
        "last_name": "Neri",
        "email": "luca@example.test",
        "is_staff": False,
        "is_superuser": False,
        "role": Role.ORGANIZER,
        "bio": "Organizer of audiovisual events.",
    },
}


class Command(BaseCommand):
    help = "Create or update deterministic demo users, events and registrations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Delete existing users and event data before recreating the "
                "demo dataset."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Registration.objects.all().delete()
            Event.objects.all().delete()
            Profile.objects.all().delete()
            get_user_model().objects.all().delete()
            self.stdout.write("Existing application data removed.")

        groups = {
            role: Group.objects.get_or_create(name=role.value)[0]
            for role in Role
        }
        users = self._seed_users(groups)
        events = self._seed_events(users)
        self._seed_registrations(users, events)

        self.stdout.write(
            self.style.SUCCESS(
                "Demo database ready: "
                f"{len(users)} users, {len(events)} events, "
                f"{Registration.objects.filter(event__in=events.values()).count()} "
                "registrations."
            )
        )

    def _seed_users(self, groups):
        user_model = get_user_model()
        users = {}

        for username, data in DEMO_USERS.items():
            user, _ = user_model.objects.update_or_create(
                username=username,
                defaults={
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "email": data["email"],
                    "is_active": True,
                    "is_staff": data["is_staff"],
                    "is_superuser": data["is_superuser"],
                },
            )
            user.set_password(data["password"])
            user.save()
            user.groups.clear()
            if data["role"] is not None:
                user.groups.add(groups[data["role"]])

            Profile.objects.update_or_create(
                user=user,
                defaults={"bio": data["bio"]},
            )
            users[username] = user

        return users

    def _seed_events(self, users):
        start = timezone.localtime(timezone.now()).replace(
            hour=18,
            minute=0,
            second=0,
            microsecond=0,
        )
        event_data = [
            {
                "key": "meetup",
                "organizer": users["organizer_demo"],
                "title": "Django Community Meetup Florence",
                "description": (
                    "Open meetup for the Django community with short talks, "
                    "a Q&A session and final networking."
                ),
                "starts_at": start + timedelta(days=10),
                "ends_at": start + timedelta(days=10, hours=3),
                "location": "Innovation Hub Firenze",
                "capacity": 40,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "full_workshop",
                "organizer": users["organizer_demo"],
                "title": "Urban Photography Workshop",
                "description": (
                    "Practical workshop about composition, light and "
                    "photographic storytelling in urban spaces."
                ),
                "starts_at": start + timedelta(days=17),
                "ends_at": start + timedelta(days=17, hours=4),
                "location": "Santa Croce Creative Space",
                "capacity": 2,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "empty_event",
                "organizer": users["organizer_demo"],
                "title": "Multimedia Production Open Day",
                "description": (
                    "Presentation of multimedia projects, tools and learning "
                    "opportunities with registration required."
                ),
                "starts_at": start + timedelta(days=24),
                "ends_at": start + timedelta(days=24, hours=2),
                "location": "Novoli Campus - Main Hall",
                "capacity": 30,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "second_organizer",
                "organizer": users["organizer2_demo"],
                "title": "Summer Audiovisual Festival 2026",
                "description": (
                    "Evening with audiovisual performances, interactive "
                    "installations and screenings curated by young authors."
                ),
                "starts_at": start + timedelta(days=31),
                "ends_at": start + timedelta(days=31, hours=5),
                "location": "Manifattura Tabacchi Florence",
                "capacity": 80,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "draft",
                "organizer": users["organizer_demo"],
                "title": "Podcast Lab - Draft",
                "description": (
                    "Event in preparation about writing, recording and "
                    "editing a podcast episode."
                ),
                "starts_at": start + timedelta(days=38),
                "ends_at": start + timedelta(days=38, hours=3),
                "location": "Media Lab Firenze",
                "capacity": 18,
                "status": Event.Status.DRAFT,
            },
            {
                "key": "cancelled",
                "organizer": users["organizer2_demo"],
                "title": "Open-Air Cinema Review - Cancelled",
                "description": (
                    "Film screening cancelled because the venue is "
                    "temporarily unavailable."
                ),
                "starts_at": start + timedelta(days=45),
                "ends_at": start + timedelta(days=45, hours=3),
                "location": "Rose Garden",
                "capacity": 100,
                "status": Event.Status.CANCELLED,
            },
        ]

        events = {}
        for data in event_data:
            key = data.pop("key")
            organizer = data.pop("organizer")
            event, _ = Event.objects.update_or_create(
                organizer=organizer,
                title=data["title"],
                defaults=data,
            )
            events[key] = event

        return events

    def _seed_registrations(self, users, events):
        desired_registrations = [
            (events["meetup"], users["attendee_demo"]),
            (events["meetup"], users["attendee2_demo"]),
            (events["full_workshop"], users["attendee_demo"]),
            (events["full_workshop"], users["attendee2_demo"]),
            (events["second_organizer"], users["attendee_demo"]),
        ]
        desired_pairs = {
            (event.pk, attendee.pk)
            for event, attendee in desired_registrations
        }

        for registration in Registration.objects.filter(
            event__in=events.values()
        ):
            if (registration.event_id, registration.attendee_id) not in (
                desired_pairs
            ):
                registration.delete()

        for event, attendee in desired_registrations:
            Registration.objects.get_or_create(
                event=event,
                attendee=attendee,
            )
