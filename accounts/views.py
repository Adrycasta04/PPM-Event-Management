from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm
from .models import Profile
from .roles import Role


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        attendee_group, _ = Group.objects.get_or_create(
            name=Role.ATTENDEE.value,
        )
        self.object.groups.add(attendee_group)
        Profile.objects.get_or_create(user=self.object)
        messages.success(
            self.request,
            "Account created successfully. You can now log in as an attendee.",
        )
        return response


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Logged in successfully.")
        return response


class UserLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Logged out successfully.")
        return response
