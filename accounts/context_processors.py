from .roles import is_attendee, is_organizer


def roles(request):
    user_is_organizer = is_organizer(request.user)
    return {
        "user_is_attendee": (
            is_attendee(request.user) and not user_is_organizer
        ),
        "user_is_organizer": user_is_organizer,
    }
