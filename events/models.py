from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class EventQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status=Event.Status.PUBLISHED)


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CANCELLED = "cancelled", "Cancelled"

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="events",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EventQuerySet.as_manager()

    class Meta:
        ordering = ["starts_at", "title"]
        constraints = [
            models.CheckConstraint(
                condition=Q(capacity__gte=1),
                name="event_capacity_at_least_one",
            ),
            models.CheckConstraint(
                condition=Q(ends_at__gt=F("starts_at")),
                name="event_ends_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "starts_at"]),
            models.Index(fields=["organizer", "starts_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError(
                {"ends_at": "The event must end after it starts."}
            )

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"pk": self.pk})

    @property
    def is_public(self):
        return self.status == self.Status.PUBLISHED

    @property
    def has_ended(self):
        return self.ends_at <= timezone.now()

    @property
    def registration_is_open(self):
        return self.is_public and self.starts_at > timezone.now()


class Registration(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "attendee"],
                name="unique_event_attendee_registration",
            ),
        ]
        indexes = [
            models.Index(fields=["event", "created_at"]),
            models.Index(fields=["attendee", "created_at"]),
        ]

    def __str__(self):
        return f"{self.attendee.get_username()} - {self.event.title}"


class Favorite(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_favorites",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_user_favorite",
            ),
        ]

    def __str__(self):
        return f"{self.user.get_username()} - {self.event.title}"


class Review(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )
    comment = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "author"],
                name="unique_event_author_review",
            ),
            models.CheckConstraint(
                condition=Q(rating__gte=1, rating__lte=5),
                name="review_rating_between_one_and_five",
            ),
        ]

    def __str__(self):
        return (
            f"{self.author.get_username()} - {self.event.title} "
            f"({self.rating}/5)"
        )

    def clean(self):
        super().clean()
        errors = {}
        if self.event_id:
            if not self.event.is_public:
                errors["event"] = "Only published events can be reviewed."
            elif not self.event.has_ended:
                errors["event"] = (
                    "Reviews are available only after the event ends."
                )
        if (
            self.event_id
            and self.author_id
            and not Registration.objects.filter(
                event_id=self.event_id,
                attendee_id=self.author_id,
            ).exists()
        ):
            errors["author"] = (
                "Only users registered for this event can leave a review."
            )
        if errors:
            raise ValidationError(errors)
