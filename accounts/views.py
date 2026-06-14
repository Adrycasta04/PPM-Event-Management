from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView


class UserLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Login effettuato con successo.")
        return response


class UserLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "Logout effettuato con successo.")
        return response
