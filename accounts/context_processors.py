from .roles import is_organizer


def roles(request):
    return {
        "user_is_organizer": is_organizer(request.user),
    }
