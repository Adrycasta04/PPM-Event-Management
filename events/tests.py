from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.roles import Role

from .models import Event, Registration


class HomePageTests(TestCase):
    def test_home_page_is_available(self):
        response = self.client.get(reverse("events:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/home.html")


class PublicEventViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="organizer",
        )
        starts_at = timezone.now() + timedelta(days=7)
        common_fields = {
            "organizer": cls.organizer,
            "description": "Event description",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Florence",
            "capacity": 50,
        }
        cls.published_event = Event.objects.create(
            title="Published event",
            status=Event.Status.PUBLISHED,
            **common_fields,
        )
        cls.draft_event = Event.objects.create(
            title="Draft event",
            status=Event.Status.DRAFT,
            **common_fields,
        )
        cls.cancelled_event = Event.objects.create(
            title="Cancelled event",
            status=Event.Status.CANCELLED,
            **common_fields,
        )

    def test_event_list_shows_only_published_events(self):
        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_list.html")
        self.assertQuerySetEqual(
            response.context["events"],
            [self.published_event],
        )
        self.assertContains(response, self.published_event.title)
        self.assertNotContains(response, self.draft_event.title)
        self.assertNotContains(response, self.cancelled_event.title)

    def test_published_event_detail_is_public(self):
        response = self.client.get(self.published_event.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_detail.html")
        self.assertEqual(response.context["event"], self.published_event)

    def test_non_public_event_details_return_not_found(self):
        for event in (self.draft_event, self.cancelled_event):
            with self.subTest(status=event.status):
                response = self.client.get(event.get_absolute_url())
                self.assertEqual(response.status_code, 404)


class EmptyEventListTests(TestCase):
    def test_event_list_has_empty_state(self):
        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Non ci sono eventi pubblicati")


class OrganizerEventCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organizer_group = Group.objects.create(name=Role.ORGANIZER.value)
        attendee_group = Group.objects.create(name=Role.ATTENDEE.value)

        cls.owner = get_user_model().objects.create_user(username="owner")
        cls.other_organizer = get_user_model().objects.create_user(
            username="other-organizer",
        )
        cls.attendee = get_user_model().objects.create_user(
            username="attendee",
        )
        cls.owner.groups.add(organizer_group)
        cls.other_organizer.groups.add(organizer_group)
        cls.attendee.groups.add(attendee_group)

    def setUp(self):
        starts_at = timezone.now() + timedelta(days=10)
        self.event = Event.objects.create(
            organizer=self.owner,
            title="Owner event",
            description="Original description",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Florence",
            capacity=30,
            status=Event.Status.DRAFT,
        )

    def form_data(self, event=None, **overrides):
        event = event or self.event
        data = {
            "title": event.title,
            "description": event.description,
            "starts_at": timezone.localtime(event.starts_at).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "ends_at": timezone.localtime(event.ends_at).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "location": event.location,
            "capacity": event.capacity,
            "status": event.status,
        }
        data.update(overrides)
        return data

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("events:create"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('events:create')}",
        )

    def test_attendee_cannot_access_organizer_pages(self):
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("events:create"), follow=True)

        self.assertRedirects(response, reverse("events:list"))
        self.assertContains(
            response,
            "Questa sezione e riservata agli organizzatori.",
        )

    def test_organizer_can_create_event_and_becomes_owner(self):
        self.client.force_login(self.owner)
        starts_at = timezone.now() + timedelta(days=20)
        data = {
            "title": "New event",
            "description": "New description",
            "starts_at": timezone.localtime(starts_at).strftime(
                "%Y-%m-%dT%H:%M"
            ),
            "ends_at": timezone.localtime(
                starts_at + timedelta(hours=3)
            ).strftime("%Y-%m-%dT%H:%M"),
            "location": "Prato",
            "capacity": 100,
            "status": Event.Status.PUBLISHED,
        }

        response = self.client.post(
            reverse("events:create"),
            data,
            follow=True,
        )

        created_event = Event.objects.get(title="New event")
        self.assertEqual(created_event.organizer, self.owner)
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(response, "Evento creato con successo.")

    def test_my_events_contains_only_events_owned_by_current_user(self):
        starts_at = timezone.now() + timedelta(days=12)
        other_event = Event.objects.create(
            organizer=self.other_organizer,
            title="Other organizer event",
            description="Other description",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Pisa",
            capacity=25,
            status=Event.Status.PUBLISHED,
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse("events:my_events"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["events"], [self.event])
        self.assertContains(response, self.event.title)
        self.assertNotContains(response, other_event.title)

    def test_owner_can_update_own_event(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("events:update", args=[self.event.pk]),
            self.form_data(title="Updated title"),
            follow=True,
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated title")
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(response, "Evento aggiornato con successo.")

    def test_other_organizer_cannot_update_event(self):
        self.client.force_login(self.other_organizer)

        response = self.client.post(
            reverse("events:update", args=[self.event.pk]),
            self.form_data(title="Unauthorized title"),
            follow=True,
        )

        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Owner event")
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(
            response,
            "Non puoi modificare o eliminare eventi di altri organizzatori.",
        )

    def test_owner_can_delete_own_event(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("events:delete", args=[self.event.pk]),
            follow=True,
        )

        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(response, "Evento eliminato con successo.")

    def test_other_organizer_cannot_delete_event(self):
        self.client.force_login(self.other_organizer)

        response = self.client.post(
            reverse("events:delete", args=[self.event.pk]),
            follow=True,
        )

        self.assertTrue(Event.objects.filter(pk=self.event.pk).exists())
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(
            response,
            "Non puoi modificare o eliminare eventi di altri organizzatori.",
        )


class AttendeeRegistrationWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        attendee_group = Group.objects.create(name=Role.ATTENDEE.value)
        organizer_group = Group.objects.create(name=Role.ORGANIZER.value)

        cls.attendee = get_user_model().objects.create_user(
            username="registration-attendee",
        )
        cls.other_attendee = get_user_model().objects.create_user(
            username="other-attendee",
        )
        cls.organizer = get_user_model().objects.create_user(
            username="registration-organizer",
        )
        cls.attendee.groups.add(attendee_group)
        cls.other_attendee.groups.add(attendee_group)
        cls.organizer.groups.add(organizer_group)

        starts_at = timezone.now() + timedelta(days=30)
        event_fields = {
            "organizer": cls.organizer,
            "description": "Registration workflow event",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Florence",
            "capacity": 2,
        }
        cls.published_event = Event.objects.create(
            title="Registration event",
            status=Event.Status.PUBLISHED,
            **event_fields,
        )
        cls.draft_event = Event.objects.create(
            title="Private draft event",
            status=Event.Status.DRAFT,
            **event_fields,
        )
        cls.cancelled_event = Event.objects.create(
            title="Cancelled registration event",
            status=Event.Status.CANCELLED,
            **event_fields,
        )

    def test_attendee_can_register_for_published_event(self):
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:register", args=[self.published_event.pk]),
            follow=True,
        )

        self.assertTrue(
            Registration.objects.filter(
                event=self.published_event,
                attendee=self.attendee,
            ).exists()
        )
        self.assertRedirects(
            response,
            self.published_event.get_absolute_url(),
        )
        self.assertContains(
            response,
            "Registrazione completata con successo.",
        )

    def test_duplicate_registration_is_prevented(self):
        Registration.objects.create(
            event=self.published_event,
            attendee=self.attendee,
        )
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:register", args=[self.published_event.pk]),
            follow=True,
        )

        self.assertEqual(
            Registration.objects.filter(
                event=self.published_event,
                attendee=self.attendee,
            ).count(),
            1,
        )
        self.assertContains(response, "Sei gia registrato a questo evento.")

    def test_registration_is_blocked_when_event_is_full(self):
        self.published_event.capacity = 1
        self.published_event.save(update_fields=["capacity"])
        Registration.objects.create(
            event=self.published_event,
            attendee=self.other_attendee,
        )
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:register", args=[self.published_event.pk]),
            follow=True,
        )

        self.assertFalse(
            Registration.objects.filter(
                event=self.published_event,
                attendee=self.attendee,
            ).exists()
        )
        self.assertContains(
            response,
            "L'evento ha raggiunto la capacita massima.",
        )

    def test_registration_is_blocked_for_non_public_events(self):
        self.client.force_login(self.attendee)

        for event in (self.draft_event, self.cancelled_event):
            with self.subTest(status=event.status):
                response = self.client.post(
                    reverse("events:register", args=[event.pk]),
                    follow=True,
                )
                self.assertFalse(
                    Registration.objects.filter(
                        event=event,
                        attendee=self.attendee,
                    ).exists()
                )
                self.assertRedirects(response, reverse("events:list"))
                self.assertContains(
                    response,
                    "Le registrazioni sono disponibili solo per eventi pubblicati.",
                )

    def test_anonymous_user_cannot_register(self):
        register_url = reverse(
            "events:register",
            args=[self.published_event.pk],
        )

        response = self.client.post(register_url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={register_url}",
        )
        self.assertEqual(Registration.objects.count(), 0)

    def test_organizer_cannot_register_as_attendee(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("events:register", args=[self.published_event.pk]),
            follow=True,
        )

        self.assertFalse(
            Registration.objects.filter(
                event=self.published_event,
                attendee=self.organizer,
            ).exists()
        )
        self.assertRedirects(response, reverse("events:list"))
        self.assertContains(
            response,
            "Questa azione e riservata agli attendee.",
        )

    def test_attendee_can_cancel_own_registration(self):
        registration = Registration.objects.create(
            event=self.published_event,
            attendee=self.attendee,
        )
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:cancel_registration", args=[registration.pk]),
            follow=True,
        )

        self.assertFalse(
            Registration.objects.filter(pk=registration.pk).exists()
        )
        self.assertRedirects(response, reverse("events:my_registrations"))
        self.assertContains(
            response,
            "Registrazione cancellata con successo.",
        )

    def test_attendee_cannot_cancel_another_users_registration(self):
        registration = Registration.objects.create(
            event=self.published_event,
            attendee=self.other_attendee,
        )
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:cancel_registration", args=[registration.pk]),
            follow=True,
        )

        self.assertTrue(
            Registration.objects.filter(pk=registration.pk).exists()
        )
        self.assertContains(
            response,
            "Non puoi cancellare la registrazione di un altro utente.",
        )

    def test_my_registrations_contains_only_current_users_records(self):
        own_registration = Registration.objects.create(
            event=self.published_event,
            attendee=self.attendee,
        )
        Registration.objects.create(
            event=self.published_event,
            attendee=self.other_attendee,
        )
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("events:my_registrations"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["registrations"],
            [own_registration],
        )


class OrganizerAttendeeListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organizer_group = Group.objects.create(name=Role.ORGANIZER.value)
        attendee_group = Group.objects.create(name=Role.ATTENDEE.value)

        cls.owner = get_user_model().objects.create_user(
            username="attendee-list-owner",
        )
        cls.other_organizer = get_user_model().objects.create_user(
            username="attendee-list-other-organizer",
        )
        cls.attendee = get_user_model().objects.create_user(
            username="listed-attendee",
            first_name="Mario",
            last_name="Rossi",
            email="mario@example.com",
        )
        cls.other_attendee = get_user_model().objects.create_user(
            username="other-listed-attendee",
        )
        cls.owner.groups.add(organizer_group)
        cls.other_organizer.groups.add(organizer_group)
        cls.attendee.groups.add(attendee_group)
        cls.other_attendee.groups.add(attendee_group)

        starts_at = timezone.now() + timedelta(days=40)
        event_fields = {
            "description": "Attendee list event",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Florence",
            "capacity": 20,
            "status": Event.Status.PUBLISHED,
        }
        cls.event = Event.objects.create(
            organizer=cls.owner,
            title="Owner attendee list event",
            **event_fields,
        )
        cls.empty_event = Event.objects.create(
            organizer=cls.owner,
            title="Empty owner event",
            **event_fields,
        )
        cls.other_event = Event.objects.create(
            organizer=cls.other_organizer,
            title="Other organizer attendee event",
            **event_fields,
        )
        cls.registration = Registration.objects.create(
            event=cls.event,
            attendee=cls.attendee,
        )
        Registration.objects.create(
            event=cls.other_event,
            attendee=cls.other_attendee,
        )

    def test_owner_can_view_attendees_for_own_event(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("events:attendees", args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_attendee_list.html")
        self.assertEqual(response.context["event"], self.event)
        self.assertQuerySetEqual(
            response.context["registrations"],
            [self.registration],
        )
        self.assertContains(response, self.attendee.username)
        self.assertContains(response, self.attendee.email)
        self.assertNotContains(response, self.other_attendee.username)

    def test_empty_event_has_clear_empty_state(self):
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse("events:attendees", args=[self.empty_event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Questo evento non ha ancora partecipanti.",
        )

    def test_other_organizer_cannot_view_attendees(self):
        self.client.force_login(self.other_organizer)

        response = self.client.get(
            reverse("events:attendees", args=[self.event.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(
            response,
            "Non puoi visualizzare i partecipanti di eventi di altri organizzatori.",
        )
        self.assertNotContains(response, self.attendee.email)

    def test_attendee_cannot_view_event_attendees(self):
        self.client.force_login(self.attendee)

        response = self.client.get(
            reverse("events:attendees", args=[self.event.pk]),
            follow=True,
        )

        self.assertRedirects(response, reverse("events:list"))
        self.assertContains(
            response,
            "Questa sezione e riservata agli organizzatori.",
        )
        self.assertNotContains(response, self.other_attendee.username)

    def test_anonymous_user_is_redirected_to_login(self):
        attendee_url = reverse("events:attendees", args=[self.event.pk])

        response = self.client.get(attendee_url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={attendee_url}",
        )
