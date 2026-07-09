from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime, time, timedelta

from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
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
                "This section is reserved for organizers.",
            )
            return redirect(self.permission_denied_url)
        return super().dispatch(request, *args, **kwargs)


class EventOwnerRequiredMixin(OrganizerRequiredMixin):
    ownership_denied_message = (
        "You cannot manage events created by other organizers."
    )

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and is_organizer(request.user)
            and not request.user.is_staff
        ):
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
        if self.request.user.is_staff:
            return Event.objects.all()
        return Event.objects.filter(organizer=self.request.user)


class AttendeeRequiredMixin(LoginRequiredMixin):
    permission_denied_url = "events:list"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not is_attendee(request.user):
            messages.error(
                request,
                "This action is reserved for registered users.",
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


class ContactView(TemplateView):
    template_name = "events/contact.html"


class EventListView(ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    time_filter_options = (
        ("all", "All events"),
        ("today", "Today"),
        ("this_week", "This week"),
        ("this_month", "This month"),
    )

    def get_queryset(self):
        queryset = (
            Event.objects.public()
            .select_related("organizer")
            .annotate(registration_count=Count("registrations"))
        )
        search_query = self.request.GET.get("q", "").strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(location__icontains=search_query)
            )

        selected_when = self._get_selected_when()
        date_range = self._get_date_range(selected_when)
        if date_range is not None:
            starts_at, ends_at = date_range
            queryset = queryset.filter(
                starts_at__gte=starts_at,
                starts_at__lt=ends_at,
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        search_query = self.request.GET.get("q", "").strip()
        selected_when = self._get_selected_when()
        context.update(
            {
                "search_query": search_query,
                "selected_when": selected_when,
                "time_filter_options": self.time_filter_options,
                "filters_active": bool(
                    search_query or selected_when != "all"
                ),
            }
        )
        return context

    def _get_selected_when(self):
        selected_when = self.request.GET.get("when", "all")
        valid_values = {value for value, _ in self.time_filter_options}
        if selected_when not in valid_values:
            return "all"
        return selected_when

    def _get_date_range(self, selected_when):
        if selected_when == "all":
            return None

        current_timezone = timezone.get_current_timezone()
        today = timezone.localdate()
        today_start = timezone.make_aware(
            datetime.combine(today, time.min),
            current_timezone,
        )

        if selected_when == "today":
            return today_start, today_start + timedelta(days=1)

        if selected_when == "this_week":
            week_start = today_start - timedelta(days=today.weekday())
            return week_start, week_start + timedelta(days=7)

        if selected_when == "this_month":
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
            return month_start, next_month_start

        return None


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
        if user.is_authenticated and is_attendee(user):
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
        queryset = Event.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(organizer=self.request.user)
        return queryset.annotate(registration_count=Count("registrations"))


class EventCreateView(OrganizerRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        messages.success(self.request, "Event created successfully.")
        return super().form_valid(form)


class EventUpdateView(EventOwnerRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        messages.success(self.request, "Event updated successfully.")
        return super().form_valid(form)


class EventDeleteView(EventOwnerRequiredMixin, DeleteView):
    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy("events:my_events")

    def form_valid(self, form):
        messages.success(self.request, "Event deleted successfully.")
        return super().form_valid(form)


class EventAttendeeListView(EventOwnerRequiredMixin, DetailView):
    model = Event
    template_name = "events/event_attendee_list.html"
    context_object_name = "event"
    ownership_denied_message = (
        "You cannot view attendees for events created by other organizers."
    )

    def get_queryset(self):
        queryset = Event.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(organizer=self.request.user)
        return queryset.prefetch_related("registrations__attendee")

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
                "Registrations are available only for published events.",
            )
            return redirect("events:list")

        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=event.pk)

            if not event.is_public:
                messages.error(
                    request,
                    "Registrations are available only for published events.",
                )
                return redirect("events:list")
            if Registration.objects.filter(
                event=event,
                attendee=request.user,
            ).exists():
                messages.warning(
                    request,
                    "You are already registered for this event.",
                )
            elif event.registrations.count() >= event.capacity:
                messages.error(
                    request,
                    "This event is full.",
                )
            else:
                Registration.objects.create(
                    event=event,
                    attendee=request.user,
                )
                messages.success(
                    request,
                    "Registration completed successfully.",
                )

        return redirect(event.get_absolute_url())


class EventRegistrationDeleteView(AttendeeRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        registration = Registration.objects.filter(pk=pk).first()

        if registration is None:
            messages.error(request, "Registration not found.")
        elif registration.attendee_id != request.user.pk:
            messages.error(
                request,
                "You cannot cancel registrations for other users.",
            )
        else:
            registration.delete()
            messages.success(
                request,
                "Registration cancelled successfully.",
            )

        return redirect("events:my_registrations")
