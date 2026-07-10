from datetime import timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.roles import Role

from .forms import EventForm
from .models import Event
from .validators import MAX_EVENT_IMAGE_SIZE, validate_event_image_size


def uploaded_image(name="event-cover.png", size=(2000, 1200), image_format="PNG"):
    output = BytesIO()
    Image.new("RGB", size, color=(36, 99, 235)).save(
        output,
        format=image_format,
    )
    content_type = f"image/{image_format.lower()}"
    return SimpleUploadedFile(name, output.getvalue(), content_type=content_type)


def valid_event_data():
    starts_at = timezone.localtime(timezone.now() + timedelta(days=7))
    return {
        "title": "Event with cover image",
        "description": "An event used to verify image upload behavior.",
        "starts_at": starts_at.strftime("%Y-%m-%dT%H:%M"),
        "ends_at": (starts_at + timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M"
        ),
        "location": "University campus",
        "capacity": 30,
        "status": Event.Status.PUBLISHED,
    }


class EventImageFormTests(TestCase):
    def test_uploaded_image_is_optimized_to_a_16_by_9_jpeg(self):
        form = EventForm(
            data=valid_event_data(),
            files={"image": uploaded_image()},
        )

        self.assertTrue(form.is_valid(), form.errors)
        optimized = form.cleaned_data["image"]
        optimized.seek(0)
        with Image.open(optimized) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, (1600, 900))
        self.assertTrue(optimized.name.endswith(".jpg"))

    def test_image_larger_than_five_megabytes_is_rejected(self):
        oversized = SimpleUploadedFile(
            "large.jpg",
            b"0" * (MAX_EVENT_IMAGE_SIZE + 1),
            content_type="image/jpeg",
        )

        with self.assertRaises(ValidationError):
            validate_event_image_size(oversized)

    def test_unsupported_image_extension_is_rejected(self):
        form = EventForm(
            data=valid_event_data(),
            files={
                "image": uploaded_image(
                    name="event-cover.gif",
                    size=(800, 450),
                    image_format="GIF",
                )
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


class OrganizerImageUploadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organizer_group = Group.objects.create(name=Role.ORGANIZER.value)
        cls.organizer = get_user_model().objects.create_user(
            username="image-organizer"
        )
        cls.organizer.groups.add(organizer_group)

    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()
        self.media_directory.cleanup()

    def test_organizer_can_create_event_with_optimized_image(self):
        self.client.force_login(self.organizer)
        data = valid_event_data()
        data["image"] = uploaded_image()

        response = self.client.post(reverse("events:create"), data, follow=True)

        event = Event.objects.get(title=data["title"])
        self.assertRedirects(response, reverse("events:my_events"))
        self.assertTrue(event.image.name.endswith(".jpg"))
        self.assertTrue(Path(event.image.path).exists())
        with Image.open(event.image.path) as image:
            self.assertEqual(image.size, (1600, 900))

    def test_event_image_is_rendered_and_served(self):
        self.client.force_login(self.organizer)
        data = valid_event_data()
        data["image"] = uploaded_image(size=(1200, 800))
        self.client.post(reverse("events:create"), data)
        event = Event.objects.get(title=data["title"])

        list_response = self.client.get(reverse("events:list"))
        detail_response = self.client.get(event.get_absolute_url())
        media_response = self.client.get(event.image.url)

        self.assertContains(list_response, event.image.url)
        self.assertContains(detail_response, event.image.url)
        self.assertEqual(media_response.status_code, 200)
        media_response.close()

    def test_event_form_uses_multipart_encoding(self):
        self.client.force_login(self.organizer)

        response = self.client.get(reverse("events:create"))

        self.assertContains(response, 'enctype="multipart/form-data"')
