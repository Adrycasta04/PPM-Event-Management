from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .roles import Role, get_user_roles, is_attendee, is_organizer


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "test-password-123"
        cls.user = get_user_model().objects.create_user(
            username="testuser",
            password=cls.password,
        )

    def test_login_page_is_available(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_user_can_log_in(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.username, "password": self.password},
            follow=True,
        )

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertRedirects(response, reverse("events:home"))
        self.assertIn(
            "Login effettuato con successo.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )

    def test_user_can_log_out_with_post(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("accounts:logout"), follow=True)

        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertRedirects(response, reverse("events:home"))
        self.assertIn(
            "Logout effettuato con successo.",
            [str(message) for message in get_messages(response.wsgi_request)],
        )


class RoleSetupTests(TestCase):
    def test_setup_roles_creates_expected_groups_idempotently(self):
        output = StringIO()

        call_command("setup_roles", stdout=output)
        call_command("setup_roles", stdout=output)

        self.assertEqual(
            set(
                Group.objects.filter(name__in=[role.value for role in Role])
                .values_list("name", flat=True)
            ),
            {Role.ATTENDEE.value, Role.ORGANIZER.value},
        )
        self.assertEqual(Group.objects.count(), 2)

    def test_role_helpers_check_group_membership(self):
        call_command("setup_roles", verbosity=0)
        user = get_user_model().objects.create_user(username="organizer")
        user.groups.add(Group.objects.get(name=Role.ORGANIZER.value))

        self.assertTrue(is_organizer(user))
        self.assertFalse(is_attendee(user))

    def test_role_helpers_reuse_group_query_for_same_user_instance(self):
        call_command("setup_roles", verbosity=0)
        user = get_user_model().objects.create_user(username="cached-organizer")
        user.groups.add(Group.objects.get(name=Role.ORGANIZER.value))

        with self.assertNumQueries(1):
            self.assertTrue(is_organizer(user))
            self.assertFalse(is_attendee(user))
            self.assertEqual(get_user_roles(user), {Role.ORGANIZER.value})

    def test_anonymous_user_has_no_application_role(self):
        from django.contrib.auth.models import AnonymousUser

        user = AnonymousUser()

        with self.assertNumQueries(0):
            self.assertFalse(is_attendee(user))
            self.assertFalse(is_organizer(user))
