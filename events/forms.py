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
            "starts_at": (
                "Inserisci sia la data sia l'orario, es. 11/09/2027 18:00."
            ),
            "ends_at": (
                "Inserisci sia la data sia l'orario, es. 11/09/2027 20:00."
            ),
            "capacity": "Numero massimo di partecipanti ammessi.",
            "status": (
                "Draft = bozza non pubblica; Published = visibile agli utenti; "
                "Cancelled = annullato/non visibile."
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

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if len(title) < 5:
            raise forms.ValidationError(
                "Il titolo deve contenere almeno 5 caratteri."
            )
        return title

    def clean_location(self):
        location = self.cleaned_data["location"].strip()
        if len(location) < 3:
            raise forms.ValidationError(
                "Il luogo deve contenere almeno 3 caratteri."
            )
        return location

    def clean_capacity(self):
        capacity = self.cleaned_data["capacity"]
        if capacity <= 0:
            raise forms.ValidationError("La capacita deve essere positiva.")
        return capacity

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get("starts_at")
        ends_at = cleaned_data.get("ends_at")

        if starts_at and ends_at and ends_at <= starts_at:
            self.add_error(
                "ends_at",
                "La fine dell'evento deve essere successiva all'inizio.",
            )

        return cleaned_data
