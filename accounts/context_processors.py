from .roles import is_attendee, is_organizer


def roles(request):
    return {
        "user_is_attendee": is_attendee(request.user),
        "user_is_organizer": is_organizer(request.user),
    }
