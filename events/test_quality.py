from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.roles import Role

from .models import Event, Registration


class RoleAndPermissionQualityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        attendee_group = Group.objects.create(name=Role.ATTENDEE.value)
        organizer_group = Group.objects.create(name=Role.ORGANIZER.value)

        cls.attendee = get_user_model().objects.create_user(
            username="quality-attendee",
        )
        cls.organizer = get_user_model().objects.create_user(
            username="quality-organizer",
        )
        cls.dual_role_user = get_user_model().objects.create_user(
            username="quality-dual-role",
        )
        cls.admin = get_user_model().objects.create_superuser(
            username="quality-admin",
            email="admin@example.com",
            password="admin-password-123",
        )
        cls.attendee.groups.add(attendee_group)
        cls.organizer.groups.add(organizer_group)
        cls.dual_role_user.groups.add(attendee_group, organizer_group)

        starts_at = timezone.now() + timedelta(days=10)
        cls.event = Event.objects.create(
            organizer=cls.organizer,
            title="Quality event",
            description="Permission quality event.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Florence",
            capacity=10,
            status=Event.Status.PUBLISHED,
        )
        cls.registration = Registration.objects.create(
            event=cls.event,
            attendee=cls.attendee,
        )

    def test_anonymous_user_is_redirected_from_all_protected_pages(self):
        protected_urls = [
            reverse("events:create"),
            reverse("events:my_events"),
            reverse("events:my_registrations"),
            reverse("events:update", args=[self.event.pk]),
            reverse("events:delete", args=[self.event.pk]),
            reverse("events:attendees", args=[self.event.pk]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('accounts:login')}?next={url}",
                )

    def test_organizer_cannot_access_attendee_workflow(self):
        self.client.force_login(self.organizer)

        for url in [
            reverse("events:my_registrations"),
            reverse("events:register", args=[self.event.pk]),
            reverse(
                "events:cancel_registration",
                args=[self.registration.pk],
            ),
        ]:
            with self.subTest(url=url):
                response = self.client.post(url, follow=True)
                self.assertRedirects(response, reverse("events:list"))
                self.assertContains(
                    response,
                    "Questa azione è riservata ai partecipanti.",
                )

    def test_user_with_both_roles_cannot_use_attendee_workflow(self):
        self.client.force_login(self.dual_role_user)

        response = self.client.post(
            reverse("events:register", args=[self.event.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("events:list"))
        self.assertFalse(
            Registration.objects.filter(
                event=self.event,
                attendee=self.dual_role_user,
            ).exists()
        )

    def test_user_with_both_roles_can_use_organizer_workflow(self):
        self.client.force_login(self.dual_role_user)

        response = self.client.get(reverse("events:create"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_form.html")

    def test_admin_has_admin_navigation_but_no_implicit_app_role(self):
        self.client.force_login(self.admin)

        home_response = self.client.get(reverse("events:home"))
        organizer_response = self.client.get(
            reverse("events:create"),
            follow=True,
        )
        attendee_response = self.client.get(
            reverse("events:my_registrations"),
            follow=True,
        )

        self.assertContains(home_response, reverse("admin:index"))
        self.assertRedirects(organizer_response, reverse("events:list"))
        self.assertRedirects(attendee_response, reverse("events:list"))

    def test_registration_mutations_reject_get_requests(self):
        self.client.force_login(self.attendee)

        self.assertEqual(
            self.client.get(
                reverse("events:register", args=[self.event.pk])
            ).status_code,
            405,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "events:cancel_registration",
                    args=[self.registration.pk],
                )
            ).status_code,
            405,
        )


class NamespacedURLTests(TestCase):
    def test_event_urls_reverse_to_expected_routes(self):
        self.assertEqual(reverse("events:home"), "/")
        self.assertEqual(reverse("events:list"), "/events/")
        self.assertEqual(reverse("events:my_events"), "/events/mine/")
        self.assertEqual(
            reverse("events:my_registrations"),
            "/registrations/mine/",
        )
        self.assertEqual(reverse("events:create"), "/events/create/")
        self.assertEqual(reverse("events:detail", args=[7]), "/events/7/")
        self.assertEqual(
            reverse("events:attendees", args=[7]),
            "/events/7/attendees/",
        )
        self.assertEqual(
            reverse("events:register", args=[7]),
            "/events/7/register/",
        )
        self.assertEqual(
            reverse("events:update", args=[7]),
            "/events/7/edit/",
        )
        self.assertEqual(
            reverse("events:delete", args=[7]),
            "/events/7/delete/",
        )
        self.assertEqual(
            reverse("events:cancel_registration", args=[9]),
            "/registrations/9/cancel/",
        )

    def test_account_urls_are_namespaced(self):
        self.assertEqual(reverse("accounts:login"), "/accounts/login/")
        self.assertEqual(reverse("accounts:logout"), "/accounts/logout/")


class PublicEventQueryEfficiencyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organizer = get_user_model().objects.create_user(
            username="query-organizer",
        )
        starts_at = timezone.now() + timedelta(days=15)
        for index in range(5):
            Event.objects.create(
                organizer=organizer,
                title=f"Query event {index}",
                description="Query efficiency event.",
                starts_at=starts_at + timedelta(days=index),
                ends_at=starts_at + timedelta(days=index, hours=2),
                location="Florence",
                capacity=20,
                status=Event.Status.PUBLISHED,
            )

    def test_public_list_avoids_per_event_queries(self):
        with self.assertNumQueries(1):
            response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["events"]), 5)
        for index in range(5):
            self.assertContains(response, f"Query event {index}")
