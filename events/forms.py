from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator

from .image_processing import optimize_event_image
from .models import Category, Event, Review
from .validators import ALLOWED_EVENT_IMAGE_EXTENSIONS


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "image",
            "category",
            "starts_at",
            "ends_at",
            "location",
            "capacity",
            "status",
        ]
        labels = {
            "title": "Title",
            "description": "Description",
            "image": "Cover image",
            "category": "Category",
            "starts_at": "Start date and time",
            "ends_at": "End date and time",
            "location": "Location",
            "capacity": "Maximum capacity",
            "status": "Status",
        }
        help_texts = {
            "starts_at": "Select both the start date and time.",
            "ends_at": "Select both the end date and time.",
            "category": "Choose the area that best describes the event.",
            "image": (
                "Optional. Upload a JPEG, PNG or WebP image up to 5 MB."
            ),
            "capacity": "Maximum number of attendees allowed.",
            "status": (
                "Draft = not public; Published = visible to users; "
                "Cancelled = not visible."
            ),
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Event name"},
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Describe the program and useful details.",
                },
            ),
            "starts_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "ends_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "location": forms.TextInput(
                attrs={"placeholder": "Venue or address"},
            ),
            "image": forms.ClearableFileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = False
        self.fields["category"].empty_label = "Other"
        for field in self.fields.values():
            css_class = (
                "form-select"
                if isinstance(field.widget, forms.Select)
                else "form-control"
            )
            field.widget.attrs["class"] = css_class

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError(
                "The title must contain at least 5 characters."
            )
        return title

    def clean_location(self):
        location = self.cleaned_data["location"].strip()
        if len(location) < 3:
            raise forms.ValidationError(
                "The location must contain at least 3 characters."
            )
        return location

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if isinstance(image, UploadedFile):
            FileExtensionValidator(
                allowed_extensions=ALLOWED_EVENT_IMAGE_EXTENSIONS
            )(image)
            return optimize_event_image(image)
        return image

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if capacity <= 0:
            raise forms.ValidationError("Capacity must be positive.")
        if self.instance.pk:
            registration_count = self.instance.registrations.count()
            if capacity < registration_count:
                raise forms.ValidationError(
                    "Capacity cannot be lower than the current number "
                    f"of registrations ({registration_count})."
                )
        return capacity

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if category is not None:
            return category
        return Category.objects.filter(slug="other").first()

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error(
                "ends_at",
                "The event must end after it starts.",
            )

        return cleaned_data


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[
            (5, "★★★★★ - Excellent (5/5)"),
            (4, "★★★★☆ - Very good (4/5)"),
            (3, "★★★☆☆ - Good (3/5)"),
            (2, "★★☆☆☆ - Fair (2/5)"),
            (1, "★☆☆☆☆ - Poor (1/5)"),
        ],
        coerce=int,
        label="Rating",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        labels = {"comment": "Review"}
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "rows": 4,
                    "maxlength": 1000,
                    "placeholder": "Share a concise and useful experience.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rating"].widget.attrs["class"] = "form-select"
        self.fields["comment"].widget.attrs["class"] = "form-control"

    def clean_comment(self):
        comment = self.cleaned_data["comment"].strip()
        if len(comment) < 10:
            raise forms.ValidationError(
                "The review must contain at least 10 characters."
            )
        return comment
