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
            "title": "Titolo",
            "description": "Descrizione",
            "starts_at": "Data e ora di inizio",
            "ends_at": "Data e ora di fine",
            "location": "Luogo",
            "capacity": "Capacita massima",
            "status": "Stato",
        }
        help_texts = {
            "capacity": "Numero massimo di partecipanti ammessi.",
            "status": (
                "Solo gli eventi pubblicati sono visibili e accettano iscrizioni."
            ),
        }
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Nome dell'evento"},
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Descrivi il programma e le informazioni utili.",
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
                attrs={"placeholder": "Sede o indirizzo"},
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
