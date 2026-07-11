from datetime import datetime, time, timedelta

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
        self.assertContains(response, "static/js/navbar-scroll.js")
        self.assertContains(response, "styles.css")
        self.assertContains(response, "hero-logo-frame")

    def test_contact_page_is_available(self):
        response = self.client.get(reverse("events:contact"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/contact.html")
        self.assertContains(response, "Explore the demo")
        self.assertContains(response, "Open GitHub Issues")
        self.assertNotContains(response, "example.com")

    def test_home_page_features_only_published_events(self):
        organizer = get_user_model().objects.create_user(
            username="home-organizer",
        )
        starts_at = timezone.now() + timedelta(days=7)
        common_fields = {
            "organizer": organizer,
            "description": "Event description",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(hours=2),
            "location": "Naples",
            "capacity": 30,
        }
        published_event = Event.objects.create(
            title="Homepage published event",
            status=Event.Status.PUBLISHED,
            **common_fields,
        )
        draft_event = Event.objects.create(
            title="Homepage draft event",
            status=Event.Status.DRAFT,
            **common_fields,
        )
        past_event = Event.objects.create(
            organizer=organizer,
            title="Homepage past event",
            description="Completed published event",
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(days=2, hours=-2),
            location="Florence",
            capacity=20,
            status=Event.Status.PUBLISHED,
        )

        response = self.client.get(reverse("events:home"))

        self.assertContains(response, published_event.title)
        self.assertNotContains(response, draft_event.title)
        self.assertNotContains(response, past_event.title)
        self.assertQuerySetEqual(
            response.context["featured_events"],
            [published_event],
        )
        self.assertEqual(
            response.context["community_stats"],
            {
                "published_events": 2,
                "upcoming_events": 1,
                "active_categories": 0,
            },
        )


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
        self.assertEqual(response.context["event"].available_capacity, 50)
        self.assertContains(response, "50 of 50 places available")

    def test_non_public_event_details_return_not_found(self):
        for event in (self.draft_event, self.cancelled_event):
            with self.subTest(status=event.status):
                response = self.client.get(event.get_absolute_url())
                self.assertEqual(response.status_code, 404)


class EventDiscoveryFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="discovery-organizer",
        )
        today = timezone.localdate()
        current_timezone = timezone.get_current_timezone()
        today_start = timezone.make_aware(
            datetime.combine(today, time.min),
            current_timezone,
        )
        week_start = today_start - timedelta(days=today.weekday())
        month_start = today_start.replace(day=1)
        if month_start.month == 12:
            next_month_start = month_start.replace(
                year=month_start.year + 1,
                month=1,
            )
        else:
            next_month_start = month_start.replace(
                month=month_start.month + 1,
            )

        week_candidate = week_start + timedelta(days=1)
        if week_candidate.date() == today:
            week_candidate = week_start + timedelta(days=2)
        if week_candidate >= week_start + timedelta(days=7):
            week_candidate = week_start

        month_candidate = week_start + timedelta(days=8)
        if month_candidate >= next_month_start:
            month_candidate = month_start

        cls.today_event = cls.create_event(
            title="AI Campus Workshop",
            description="Hands-on session about artificial intelligence.",
            location="Innovation Classroom",
            starts_at=today_start + timedelta(hours=12),
        )
        cls.week_event = cls.create_event(
            title="Study Group Sprint",
            description="Collaborative exam preparation for students.",
            location="Library Room B",
            starts_at=week_candidate + timedelta(hours=14),
        )
        cls.month_event = cls.create_event(
            title="Career CV Clinic",
            description="Career services workshop for student resumes.",
            location="Career Hub",
            starts_at=month_candidate + timedelta(hours=10),
        )
        cls.next_month_event = cls.create_event(
            title="Next Month Seminar",
            description="Seminar scheduled outside the current month.",
            location="Future Hall",
            starts_at=next_month_start + timedelta(days=2, hours=9),
        )
        cls.draft_event = cls.create_event(
            title="Hidden AI Draft",
            description="Draft event matching the search keyword.",
            location="Innovation Classroom",
            starts_at=today_start + timedelta(hours=15),
            status=Event.Status.DRAFT,
        )
        cls.cancelled_event = cls.create_event(
            title="Cancelled AI Event",
            description="Cancelled event matching the search keyword.",
            location="Innovation Classroom",
            starts_at=today_start + timedelta(hours=16),
            status=Event.Status.CANCELLED,
        )

    @classmethod
    def create_event(
        cls,
        title,
        description,
        location,
        starts_at,
        status=Event.Status.PUBLISHED,
    ):
        return Event.objects.create(
            organizer=cls.organizer,
            title=title,
            description=description,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location=location,
            capacity=30,
            status=status,
        )

    def assert_events(self, response, expected_events):
        self.assertQuerySetEqual(
            response.context["events"],
            expected_events,
        )

    def test_search_by_event_title(self):
        response = self.client.get(reverse("events:list"), {"q": "campus"})

        self.assert_events(response, [self.today_event])
        self.assertContains(response, 'value="campus"')

    def test_search_by_description(self):
        response = self.client.get(reverse("events:list"), {"q": "resumes"})

        self.assert_events(response, [self.month_event])

    def test_search_by_location(self):
        response = self.client.get(reverse("events:list"), {"q": "library"})

        self.assert_events(response, [self.week_event])

    def test_search_excludes_draft_and_cancelled_events(self):
        response = self.client.get(reverse("events:list"), {"q": "AI"})

        self.assert_events(response, [self.today_event])
        self.assertNotContains(response, self.draft_event.title)
        self.assertNotContains(response, self.cancelled_event.title)

    def test_today_filter(self):
        response = self.client.get(
            reverse("events:list"),
            {"when": "today"},
        )

        self.assert_events(response, [self.today_event])

    def test_this_week_filter(self):
        response = self.client.get(
            reverse("events:list"),
            {"when": "this_week"},
        )

        self.assertIn(self.today_event, response.context["events"])
        self.assertIn(self.week_event, response.context["events"])
        self.assertNotIn(self.next_month_event, response.context["events"])

    def test_this_month_filter(self):
        response = self.client.get(
            reverse("events:list"),
            {"when": "this_month"},
        )

        self.assertIn(self.today_event, response.context["events"])
        self.assertIn(self.month_event, response.context["events"])
        self.assertNotIn(self.next_month_event, response.context["events"])

    def test_invalid_time_filter_falls_back_to_all_events(self):
        response = self.client.get(
            reverse("events:list"),
            {"when": "unsupported"},
        )

        self.assertEqual(response.context["selected_when"], "all")
        self.assertIn(self.next_month_event, response.context["events"])

    def test_search_and_time_filter_work_together(self):
        response = self.client.get(
            reverse("events:list"),
            {"q": "career", "when": "this_month"},
        )

        self.assert_events(response, [self.month_event])


class EmptyEventListTests(TestCase):
    def test_event_list_has_empty_state(self):
        response = self.client.get(reverse("events:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "There are no published events")


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
            "This section is reserved for organizers.",
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
        self.assertContains(response, "Event created successfully.")

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
        self.assertContains(response, "Event updated successfully.")

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
            "You cannot manage events created by other organizers.",
        )

    def test_owner_can_delete_own_event(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("events:delete", args=[self.event.pk]),
            follow=True,
        )

        self.assertFalse(Event.objects.filter(pk=self.event.pk).exists())
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertContains(response, "Event deleted successfully.")

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
            "You cannot manage events created by other organizers.",
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
            "Registration completed successfully.",
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
        self.assertContains(response, "You are already registered for this event.")

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
            "This event is full.",
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
                    "Registrations are available only for published events.",
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

    def test_organizer_can_register_as_attendee(self):
        self.client.force_login(self.organizer)

        response = self.client.post(
            reverse("events:register", args=[self.published_event.pk]),
            follow=True,
        )

        self.assertTrue(
            Registration.objects.filter(
                event=self.published_event,
                attendee=self.organizer,
            ).exists()
        )
        self.assertRedirects(response, self.published_event.get_absolute_url())
        self.assertContains(
            response,
            "Registration completed successfully.",
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
            "Registration cancelled successfully.",
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
            "You cannot cancel registrations for other users.",
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
            "This event has no attendees yet.",
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
            "You cannot view attendees for events created by other organizers.",
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
            "This section is reserved for organizers.",
        )
        self.assertNotContains(response, self.other_attendee.username)

    def test_anonymous_user_is_redirected_to_login(self):
        attendee_url = reverse("events:attendees", args=[self.event.pk])

        response = self.client.get(attendee_url)

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={attendee_url}",
        )
