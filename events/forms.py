from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "starts_at",
            "ends_at",
            "location",
            "capacity",
            "status",
        ]
        labels = {
            "title": "Title",
            "description": "Description",
            "starts_at": "Start date and time",
            "ends_at": "End date and time",
            "location": "Location",
            "capacity": "Maximum capacity",
            "status": "Status",
        }
        help_texts = {
            "starts_at": "Select both the start date and time.",
            "ends_at": "Select both the end date and time.",
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
