from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Profile
from accounts.roles import Role

from .models import Category, Event, Favorite, Registration, Review


class CategoryDiscoveryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organizer = get_user_model().objects.create_user(
            username="category-organizer"
        )
        cls.technology = Category.objects.get(slug="technology")
        cls.social = Category.objects.get(slug="social")
        starts_at = timezone.now() + timedelta(days=7)
        cls.technology_event = Event.objects.create(
            organizer=cls.organizer,
            category=cls.technology,
            title="Campus coding workshop",
            description="A practical technology event.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Computer lab",
            capacity=20,
            status=Event.Status.PUBLISHED,
        )
        cls.social_event = Event.objects.create(
            organizer=cls.organizer,
            category=cls.social,
            title="International student social",
            description="A social event for the campus community.",
            starts_at=starts_at + timedelta(days=1),
            ends_at=starts_at + timedelta(days=1, hours=2),
            location="Student union",
            capacity=30,
            status=Event.Status.PUBLISHED,
        )
        Event.objects.create(
            organizer=cls.organizer,
            category=cls.technology,
            title="Private technology draft",
            description="This event must remain private.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Computer lab",
            capacity=20,
            status=Event.Status.DRAFT,
        )

    def test_category_filter_returns_only_matching_published_events(self):
        response = self.client.get(
            reverse("events:list"),
            {"category": self.technology.slug},
        )

        self.assertQuerySetEqual(
            response.context["events"],
            [self.technology_event],
        )
        self.assertContains(response, self.technology_event.title)
        self.assertNotContains(response, self.social_event.title)
        self.assertNotContains(response, "Private technology draft")

    def test_category_filter_works_with_text_search(self):
        response = self.client.get(
            reverse("events:list"),
            {"category": self.social.slug, "q": "student"},
        )

        self.assertQuerySetEqual(response.context["events"], [self.social_event])

    def test_invalid_category_safely_falls_back_to_all_events(self):
        response = self.client.get(
            reverse("events:list"),
            {"category": "not-a-category"},
        )

        self.assertQuerySetEqual(
            response.context["events"],
            [self.technology_event, self.social_event],
            ordered=False,
        )


class OrganizerPublicHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        attendee_group = Group.objects.get_or_create(
            name=Role.ATTENDEE.value
        )[0]
        cls.attendee = get_user_model().objects.create_user(
            username="history-attendee"
        )
        cls.attendee.groups.add(attendee_group)
        cls.organizer = get_user_model().objects.create_user(
            username="history-organizer"
        )
        Profile.objects.create(
            user=cls.organizer,
            bio="Student activities and community events.",
        )
        cls.other_organizer = get_user_model().objects.create_user(
            username="history-other-organizer"
        )
        now = timezone.now()
        event_fields = {
            "organizer": cls.organizer,
            "description": "Organizer history event.",
            "location": "University campus",
            "capacity": 30,
        }
        cls.current_event = Event.objects.create(
            title="Upcoming organizer event",
            starts_at=now + timedelta(days=5),
            ends_at=now + timedelta(days=5, hours=2),
            status=Event.Status.PUBLISHED,
            **event_fields,
        )
        cls.past_event = Event.objects.create(
            title="Past organizer event",
            starts_at=now - timedelta(days=5),
            ends_at=now - timedelta(days=5, hours=-2),
            status=Event.Status.PUBLISHED,
            **event_fields,
        )
        cls.draft_event = Event.objects.create(
            title="Private organizer draft",
            starts_at=now + timedelta(days=8),
            ends_at=now + timedelta(days=8, hours=2),
            status=Event.Status.DRAFT,
            **event_fields,
        )
        cls.cancelled_event = Event.objects.create(
            title="Cancelled organizer event",
            starts_at=now + timedelta(days=9),
            ends_at=now + timedelta(days=9, hours=2),
            status=Event.Status.CANCELLED,
            **event_fields,
        )
        cls.other_event = Event.objects.create(
            organizer=cls.other_organizer,
            title="Other organizer event history",
            description="An event owned by another organizer.",
            starts_at=now + timedelta(days=6),
            ends_at=now + timedelta(days=6, hours=2),
            location="University campus",
            capacity=30,
            status=Event.Status.PUBLISHED,
        )

    def test_attendee_can_view_organizer_published_event_history(self):
        self.client.force_login(self.attendee)

        response = self.client.get(
            reverse("events:organizer_history", args=[self.organizer.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "events/organizer_event_history.html",
        )
        self.assertQuerySetEqual(
            response.context["current_events"],
            [self.current_event],
        )
        self.assertQuerySetEqual(
            response.context["past_events"],
            [self.past_event],
        )
        self.assertEqual(
            response.context["organizer_bio"],
            "Student activities and community events.",
        )
        self.assertContains(response, "@history-organizer")
        self.assertContains(response, "Student activities and community events.")

    def test_history_excludes_private_and_other_organizer_events(self):
        response = self.client.get(
            reverse("events:organizer_history", args=[self.organizer.pk])
        )

        self.assertContains(response, self.current_event.title)
        self.assertContains(response, self.past_event.title)
        self.assertNotContains(response, self.draft_event.title)
        self.assertNotContains(response, self.cancelled_event.title)
        self.assertNotContains(response, self.other_event.title)

    def test_event_pages_link_to_organizer_history(self):
        history_url = reverse(
            "events:organizer_history",
            args=[self.organizer.pk],
        )

        list_response = self.client.get(reverse("events:list"))
        detail_response = self.client.get(self.current_event.get_absolute_url())

        self.assertContains(list_response, history_url)
        self.assertContains(detail_response, history_url)

    def test_user_without_published_events_has_no_public_history(self):
        user_without_events = get_user_model().objects.create_user(
            username="history-no-events"
        )

        response = self.client.get(
            reverse(
                "events:organizer_history",
                args=[user_without_events.pk],
            )
        )

        self.assertEqual(response.status_code, 404)


class FavoriteWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        attendee_group = Group.objects.get_or_create(
            name=Role.ATTENDEE.value
        )[0]
        organizer_group = Group.objects.get_or_create(
            name=Role.ORGANIZER.value
        )[0]
        cls.attendee = get_user_model().objects.create_user(
            username="favorite-attendee"
        )
        cls.organizer = get_user_model().objects.create_user(
            username="favorite-event-organizer"
        )
        cls.admin = get_user_model().objects.create_superuser(
            username="favorite-admin",
            email="favorite-admin@example.com",
            password="admin-password-123",
        )
        cls.attendee.groups.add(attendee_group)
        cls.organizer.groups.add(organizer_group)
        starts_at = timezone.now() + timedelta(days=5)
        cls.event = Event.objects.create(
            organizer=cls.organizer,
            category=Category.objects.get(slug="social"),
            title="Favorite workflow event",
            description="A published event that can be saved.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Student union",
            capacity=30,
            status=Event.Status.PUBLISHED,
        )
        cls.draft = Event.objects.create(
            organizer=cls.organizer,
            title="Favorite draft event",
            description="A private event.",
            starts_at=starts_at,
            ends_at=starts_at + timedelta(hours=2),
            location="Student union",
            capacity=30,
            status=Event.Status.DRAFT,
        )

    def test_attendee_can_add_and_remove_favorite(self):
        self.client.force_login(self.attendee)
        url = reverse("events:toggle_favorite", args=[self.event.pk])

        add_response = self.client.post(url, follow=True)
        self.assertTrue(Favorite.objects.filter(event=self.event, user=self.attendee).exists())
        self.assertContains(add_response, "Event added to your favorites.")

        remove_response = self.client.post(url, follow=True)
        self.assertFalse(Favorite.objects.filter(event=self.event, user=self.attendee).exists())
        self.assertContains(remove_response, "Event removed from your favorites.")

    def test_organizer_can_favorite_an_owned_event(self):
        self.client.force_login(self.organizer)
        detail_url = self.event.get_absolute_url()
        favorite_url = reverse(
            "events:toggle_favorite",
            args=[self.event.pk],
        )

        detail_response = self.client.get(detail_url)
        add_response = self.client.post(favorite_url, follow=True)
        favorites_response = self.client.get(
            reverse("events:my_favorites")
        )

        self.assertContains(detail_response, "Add to favorites")
        self.assertContains(detail_response, "Edit")
        self.assertTrue(
            Favorite.objects.filter(
                event=self.event,
                user=self.organizer,
            ).exists()
        )
        self.assertContains(add_response, "Event added to your favorites.")
        self.assertContains(favorites_response, self.event.title)

    def test_admin_can_favorite_an_event(self):
        self.client.force_login(self.admin)
        detail_url = self.event.get_absolute_url()
        favorite_url = reverse(
            "events:toggle_favorite",
            args=[self.event.pk],
        )

        detail_response = self.client.get(detail_url)
        add_response = self.client.post(favorite_url, follow=True)
        favorites_response = self.client.get(
            reverse("events:my_favorites")
        )

        self.assertContains(detail_response, "Add to favorites")
        self.assertContains(detail_response, "Edit")
        self.assertTrue(
            Favorite.objects.filter(
                event=self.event,
                user=self.admin,
            ).exists()
        )
        self.assertContains(add_response, "Event added to your favorites.")
        self.assertContains(favorites_response, self.event.title)

    def test_anonymous_user_is_redirected_to_login(self):
        url = reverse("events:toggle_favorite", args=[self.event.pk])

        response = self.client.post(url)

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_non_public_event_cannot_be_favorited(self):
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:toggle_favorite", args=[self.draft.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Favorite.objects.filter(event=self.draft).exists())

    def test_my_favorites_contains_only_current_users_public_events(self):
        Favorite.objects.create(event=self.event, user=self.attendee)
        Favorite.objects.create(event=self.event, user=self.organizer)
        Favorite.objects.create(event=self.draft, user=self.attendee)
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("events:my_favorites"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["favorites"]), 1)
        self.assertContains(response, self.event.title)
        self.assertNotContains(response, self.draft.title)


class ReviewWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        attendee_group = Group.objects.get_or_create(
            name=Role.ATTENDEE.value
        )[0]
        organizer_group = Group.objects.get_or_create(
            name=Role.ORGANIZER.value
        )[0]
        cls.attendee = get_user_model().objects.create_user(
            username="review-attendee"
        )
        cls.other_attendee = get_user_model().objects.create_user(
            username="review-other-attendee"
        )
        cls.organizer = get_user_model().objects.create_user(
            username="review-event-organizer"
        )
        cls.attendee.groups.add(attendee_group)
        cls.other_attendee.groups.add(attendee_group)
        cls.organizer.groups.add(organizer_group)
        past_start = timezone.now() - timedelta(days=3)
        future_start = timezone.now() + timedelta(days=3)
        cls.past_event = Event.objects.create(
            organizer=cls.organizer,
            category=Category.objects.get(slug="culture"),
            title="Completed cultural event",
            description="A completed event ready for participant feedback.",
            starts_at=past_start,
            ends_at=past_start + timedelta(hours=2),
            location="Student auditorium",
            capacity=30,
            status=Event.Status.PUBLISHED,
        )
        cls.future_event = Event.objects.create(
            organizer=cls.organizer,
            category=Category.objects.get(slug="technology"),
            title="Future technology event",
            description="An event that has not happened yet.",
            starts_at=future_start,
            ends_at=future_start + timedelta(hours=2),
            location="Computer lab",
            capacity=30,
            status=Event.Status.PUBLISHED,
        )
        Registration.objects.create(event=cls.past_event, attendee=cls.attendee)
        Registration.objects.create(event=cls.future_event, attendee=cls.attendee)

    def test_registered_attendee_can_review_completed_event(self):
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:save_review", args=[self.past_event.pk]),
            {"rating": 5, "comment": "A useful and well organized event."},
            follow=True,
        )

        review = Review.objects.get(event=self.past_event, author=self.attendee)
        self.assertEqual(review.rating, 5)
        self.assertContains(response, "Your review has been saved.")

    def test_reviewing_future_event_is_blocked(self):
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:save_review", args=[self.future_event.pk]),
            {"rating": 5, "comment": "This should not be accepted yet."},
            follow=True,
        )

        self.assertFalse(Review.objects.filter(event=self.future_event).exists())
        self.assertContains(
            response,
            "Reviews are available only after the event ends.",
        )

    def test_unregistered_attendee_cannot_review_completed_event(self):
        self.client.force_login(self.other_attendee)

        response = self.client.post(
            reverse("events:save_review", args=[self.past_event.pk]),
            {"rating": 4, "comment": "I should not be able to post this."},
            follow=True,
        )

        self.assertFalse(
            Review.objects.filter(
                event=self.past_event,
                author=self.other_attendee,
            ).exists()
        )
        self.assertContains(
            response,
            "Only registered participants can review this event.",
        )

    def test_submitting_again_updates_existing_review(self):
        Review.objects.create(
            event=self.past_event,
            author=self.attendee,
            rating=3,
            comment="The original participant review.",
        )
        self.client.force_login(self.attendee)

        self.client.post(
            reverse("events:save_review", args=[self.past_event.pk]),
            {"rating": 5, "comment": "The updated participant review."},
        )

        self.assertEqual(
            Review.objects.filter(
                event=self.past_event,
                author=self.attendee,
            ).count(),
            1,
        )
        self.assertEqual(
            Review.objects.get(
                event=self.past_event,
                author=self.attendee,
            ).rating,
            5,
        )

    def test_attendee_can_delete_only_own_review(self):
        own_review = Review.objects.create(
            event=self.past_event,
            author=self.attendee,
            rating=4,
            comment="A review that will be deleted.",
        )
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("events:delete_review", args=[own_review.pk]),
            follow=True,
        )

        self.assertFalse(Review.objects.filter(pk=own_review.pk).exists())
        self.assertContains(response, "Your review has been deleted.")

    def test_attendee_cannot_delete_another_users_review(self):
        other_review = Review.objects.create(
            event=self.past_event,
            author=self.attendee,
            rating=4,
            comment="Another participant owns this review.",
        )
        self.client.force_login(self.other_attendee)

        response = self.client.post(
            reverse("events:delete_review", args=[other_review.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=other_review.pk).exists())

    def test_event_detail_displays_public_reviews(self):
        Review.objects.create(
            event=self.past_event,
            author=self.attendee,
            rating=4,
            comment="A visible review for other students.",
        )

        response = self.client.get(self.past_event.get_absolute_url())

        self.assertContains(response, "A visible review for other students.")
        self.assertContains(response, "4/5")
        self.assertContains(response, "★★★★☆")

    def test_registration_and_cancellation_are_blocked_after_event(self):
        self.client.force_login(self.other_attendee)
        register_response = self.client.post(
            reverse("events:register", args=[self.past_event.pk]),
            follow=True,
        )
        self.assertFalse(
            Registration.objects.filter(
                event=self.past_event,
                attendee=self.other_attendee,
            ).exists()
        )
        self.assertContains(
            register_response,
            "Registrations close when the event starts.",
        )

        self.client.force_login(self.attendee)
        registration = Registration.objects.get(
            event=self.past_event,
            attendee=self.attendee,
        )
        cancel_response = self.client.post(
            reverse("events:cancel_registration", args=[registration.pk]),
            follow=True,
        )
        self.assertTrue(Registration.objects.filter(pk=registration.pk).exists())
        self.assertContains(
            cancel_response,
            "Registrations cannot be cancelled after the event starts.",
        )
