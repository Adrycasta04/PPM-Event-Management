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
                "legacy_titles": ("Django Community Meetup Florence",),
                "organizer": users["organizer_demo"],
                "title": "Django Workshop for Beginners",
                "description": (
                    "Introductory workshop for students who want to build "
                    "their first Django app with models, forms and templates."
                ),
                "starts_at": start + timedelta(days=10),
                "ends_at": start + timedelta(days=10, hours=3),
                "location": "Computer Science Lab 2",
                "capacity": 40,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "full_workshop",
                "legacy_titles": ("Urban Photography Workshop",),
                "organizer": users["organizer_demo"],
                "title": "CV and LinkedIn Lab",
                "description": (
                    "Small career workshop for students who want feedback on "
                    "their CV, LinkedIn profile and internship applications."
                ),
                "starts_at": start + timedelta(days=17),
                "ends_at": start + timedelta(days=17, hours=2),
                "location": "Career Services Room",
                "capacity": 2,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "empty_event",
                "legacy_titles": ("Multimedia Production Open Day",),
                "organizer": users["organizer_demo"],
                "title": "Erasmus Welcome Aperitivo",
                "description": (
                    "Informal welcome event for Erasmus and international "
                    "students with introductions, campus tips and networking."
                ),
                "starts_at": start + timedelta(days=24),
                "ends_at": start + timedelta(days=24, hours=3),
                "location": "Student Union Terrace",
                "capacity": 45,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "second_organizer",
                "legacy_titles": ("Summer Audiovisual Festival 2026",),
                "organizer": users["organizer2_demo"],
                "title": "International Students Meetup",
                "description": (
                    "Community meetup for international and local students "
                    "with group activities and practical university advice."
                ),
                "starts_at": start + timedelta(days=31),
                "ends_at": start + timedelta(days=31, hours=3),
                "location": "Student Community Center",
                "capacity": 80,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "design_conference",
                "legacy_titles": ("Digital Design Conference",),
                "organizer": users["organizer_demo"],
                "title": "AI & Machine Learning Seminar",
                "description": (
                    "University seminar introducing machine learning concepts, "
                    "student project examples and ethical AI discussion."
                ),
                "starts_at": start + timedelta(days=34),
                "ends_at": start + timedelta(days=34, hours=2),
                "location": "Engineering Auditorium",
                "capacity": 60,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "backend_bootcamp",
                "legacy_titles": ("Backend Development Bootcamp",),
                "organizer": users["organizer2_demo"],
                "title": "Hackathon: Build for Campus",
                "description": (
                    "One-day student hackathon to design small digital tools "
                    "that improve campus life and study organization."
                ),
                "starts_at": start + timedelta(days=36),
                "ends_at": start + timedelta(days=36, hours=5),
                "location": "University Innovation Hub",
                "capacity": 35,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "sports_tournament",
                "legacy_titles": (),
                "organizer": users["organizer2_demo"],
                "title": "Student Five-a-Side Tournament",
                "description": (
                    "Friendly football tournament for student teams, with "
                    "short matches and a final social gathering."
                ),
                "starts_at": start + timedelta(days=39),
                "ends_at": start + timedelta(days=39, hours=4),
                "location": "University Sports Center",
                "capacity": 50,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "study_group",
                "legacy_titles": (),
                "organizer": users["organizer_demo"],
                "title": "Algorithms Study Group",
                "description": (
                    "Peer study session for students preparing algorithms and "
                    "data structures exams with guided exercises."
                ),
                "starts_at": start + timedelta(days=41),
                "ends_at": start + timedelta(days=41, hours=2),
                "location": "Science Library Study Room",
                "capacity": 25,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "student_party",
                "legacy_titles": (),
                "organizer": users["organizer2_demo"],
                "title": "Summer Student Party",
                "description": (
                    "End-of-semester social evening for students with music, "
                    "informal networking and community activities."
                ),
                "starts_at": start + timedelta(days=43),
                "ends_at": start + timedelta(days=43, hours=5),
                "location": "Student Union Courtyard",
                "capacity": 120,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "photography_walk",
                "legacy_titles": (),
                "organizer": users["organizer_demo"],
                "title": "Photography Walk in Florence",
                "description": (
                    "Creative activity for students interested in photography, "
                    "urban observation and visual storytelling."
                ),
                "starts_at": start + timedelta(days=46),
                "ends_at": start + timedelta(days=46, hours=3),
                "location": "Piazza Santissima Annunziata",
                "capacity": 20,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "cinema_night",
                "legacy_titles": (),
                "organizer": users["organizer2_demo"],
                "title": "Cinema Night at the Student Union",
                "description": (
                    "Cultural evening with a student-selected film screening "
                    "and an open discussion after the movie."
                ),
                "starts_at": start + timedelta(days=48),
                "ends_at": start + timedelta(days=48, hours=3),
                "location": "Student Union Auditorium",
                "capacity": 70,
                "status": Event.Status.PUBLISHED,
            },
            {
                "key": "career_day",
                "legacy_titles": ("Creative Technology Career Day",),
                "organizer": users["organizer_demo"],
                "title": "UNIFI Career Day - Cancelled",
                "description": (
                    "Cancelled career event with companies, alumni and "
                    "internship opportunities for university students."
                ),
                "starts_at": start + timedelta(days=50),
                "ends_at": start + timedelta(days=50, hours=4),
                "location": "Career Services Hall",
                "capacity": 120,
                "status": Event.Status.CANCELLED,
            },
            {
                "key": "draft",
                "legacy_titles": ("Podcast Lab - Draft",),
                "organizer": users["organizer_demo"],
                "title": "Student Radio Podcast Lab - Draft",
                "description": (
                    "Draft study activity about writing, recording and "
                    "editing a podcast episode for student media."
                ),
                "starts_at": start + timedelta(days=52),
                "ends_at": start + timedelta(days=52, hours=3),
                "location": "Student Media Lab",
                "capacity": 18,
                "status": Event.Status.DRAFT,
            },
            {
                "key": "cancelled",
                "legacy_titles": ("Open-Air Cinema Review - Cancelled",),
                "organizer": users["organizer2_demo"],
                "title": "Campus Volunteering Fair - Cancelled",
                "description": (
                    "Cancelled fair for student associations and volunteering "
                    "groups because the venue is temporarily unavailable."
                ),
                "starts_at": start + timedelta(days=54),
                "ends_at": start + timedelta(days=54, hours=3),
                "location": "Main Campus Garden",
                "capacity": 100,
                "status": Event.Status.CANCELLED,
            },
        ]

        events = {}
        for data in event_data:
            key = data.pop("key")
            legacy_titles = data.pop("legacy_titles")
            organizer = data.pop("organizer")
            event = (
                Event.objects.filter(
                    organizer=organizer,
                    title__in=(data["title"], *legacy_titles),
                )
                .order_by("pk")
                .first()
            )
            if event is None:
                event = Event(organizer=organizer)
            event.organizer = organizer
            for field, value in data.items():
                setattr(event, field, value)
            event.save()
            events[key] = event

        return events

    def _seed_registrations(self, users, events):
        desired_registrations = [
            (events["meetup"], users["attendee_demo"]),
            (events["meetup"], users["attendee2_demo"]),
            (events["full_workshop"], users["attendee_demo"]),
            (events["full_workshop"], users["attendee2_demo"]),
            (events["second_organizer"], users["attendee_demo"]),
            (events["design_conference"], users["attendee2_demo"]),
            (events["backend_bootcamp"], users["organizer_demo"]),
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
