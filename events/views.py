from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from accounts.roles import is_attendee, is_organizer

from .forms import EventForm
from .models import Event, Registration


class OrganizerRequiredMixin(LoginRequiredMixin):
    permission_denied_url = "events:list"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not is_organizer(request.user):
            messages.error(
                request,
                "Questa sezione è riservata agli organizzatori.",
            )
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class EventOwnerRequiredMixin(OrganizerRequiredMixin):
    ownership_denied_message = (
        "Non puoi modificare o eliminare eventi di altri organizzatori."
    )

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
                    self.ownership_denied_message,
                )
                return redirect("events:my_events")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Event.objects.filter(organizer=self.request.user)


class AttendeeRequiredMixin(LoginRequiredMixin):
    permission_denied_url = "events:list"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and (
            not is_attendee(request.user) or is_organizer(request.user)
        ):
            messages.error(
                request,
                "Questa azione è riservata ai partecipanti.",
            )
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class HomeView(TemplateView):
    template_name = "events/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["featured_events"] = (
            Event.objects.public()
            .select_related("organizer")
            .annotate(registration_count=Count("registrations"))[:3]
        )
        return context


class EventListView(ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return (
            Event.objects.public()
            .select_related("organizer")
            .annotate(registration_count=Count("registrations"))
        )


class EventDetailView(DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return (
            Event.objects.public()
            .select_related("organizer")
            .annotate(registration_count=Count("registrations"))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if (
            user.is_authenticated
            and is_attendee(user)
            and not is_organizer(user)
        ):
            registration = Registration.objects.filter(
                event=self.object,
                attendee=user,
            ).first()
            context["registration"] = registration
            context["event_is_full"] = (
                self.object.registration_count >= self.object.capacity
            )
        return context


class MyEventListView(OrganizerRequiredMixin, ListView):
    model = Event
    template_name = "events/my_event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(
            organizer=self.request.user,
        ).annotate(registration_count=Count("registrations"))


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


class EventAttendeeListView(EventOwnerRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_attendee_list.html"
    context_object_name = "event"
    ownership_denied_message = (
        "Non puoi visualizzare i partecipanti di eventi di altri organizzatori."
    )

    def get_queryset(self):
        return Event.objects.filter(
            organizer=self.request.user,
        ).prefetch_related("registrations__attendee")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["registrations"] = self.object.registrations.all()
        return context


class MyRegistrationListView(AttendeeRequiredMixin, ListView):
    model = Registration
    template_name = "events/my_registration_list.html"
    context_object_name = "registrations"

    def get_queryset(self):
        return (
            Registration.objects.filter(attendee=self.request.user)
            .select_related("event", "event__organizer")
        )


class EventRegistrationCreateView(AttendeeRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        if not event.is_public:
            messages.error(
                request,
                "Le registrazioni sono disponibili solo per eventi pubblicati.",
            )
            return redirect("events:list")

        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=event.pk)

            if not event.is_public:
                messages.error(
                    request,
                    "Le registrazioni sono disponibili solo per eventi pubblicati.",
                )
                return redirect("events:list")
            if Registration.objects.filter(
                event=event,
                attendee=request.user,
            ).exists():
                messages.warning(
                    request,
                    "Sei già registrato a questo evento.",
                )
            elif event.registrations.count() >= event.capacity:
                messages.error(
                    request,
                    "L'evento ha raggiunto la capacità massima.",
                )
            else:
                Registration.objects.create(
                    event=event,
                    attendee=request.user,
                )
                messages.success(
                    request,
                    "Iscrizione completata con successo.",
                )

        return redirect(event.get_absolute_url())


class EventRegistrationDeleteView(AttendeeRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        registration = Registration.objects.filter(pk=pk).first()

        if registration is None:
            messages.error(request, "Iscrizione non trovata.")
        elif registration.attendee_id != request.user.pk:
            messages.error(
                request,
                "Non puoi annullare iscrizioni di altri utenti.",
            )
        else:
            registration.delete()
            messages.success(
                request,
                "Iscrizione annullata con successo.",
            )

        return redirect("events:my_registrations")
