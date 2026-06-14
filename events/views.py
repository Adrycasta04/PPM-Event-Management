from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from accounts.roles import is_organizer

from .forms import EventForm
from .models import Event


class OrganizerRequiredMixin(LoginRequiredMixin):
    permission_denied_url = "events:list"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not is_organizer(request.user):
            messages.error(
                request,
                "Questa sezione e riservata agli organizzatori.",
            )
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class EventOwnerRequiredMixin(OrganizerRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and is_organizer(request.user):
            event = (
                Event.objects.filter(pk=kwargs.get("pk"))
                .only("organizer_id")
                .first()
            )
            if event is not None and event.organizer_id != request.user.pk:
                messages.error(
                    request,
                    "Non puoi modificare o eliminare eventi di altri organizzatori.",
                )
                return redirect("events:my_events")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class HomeView(TemplateView):
    template_name = "events/home.html"


class EventListView(ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.public().select_related("organizer")


class EventDetailView(DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.public().select_related("organizer")


class MyEventListView(OrganizerRequiredMixin, ListView):
    model = Event
    template_name = "events/my_event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class EventCreateView(OrganizerRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, "Evento creato con successo.")
        return super().form_valid(form)


class EventUpdateView(EventOwnerRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        messages.success(self.request, "Evento aggiornato con successo.")
        return super().form_valid(form)


class EventDeleteView(EventOwnerRequiredMixin, DeleteView):
    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        messages.success(self.request, "Evento eliminato con successo.")
        return super().form_valid(form)
