from enum import StrEnum


class Role(StrEnum):
    ATTENDEE = "Attendee"
    ORGANIZER = "Organizer"


def get_user_roles(user):
    if not user.is_authenticated:
        return frozenset()

    if not hasattr(user, "_ppm_role_names"):
        user._ppm_role_names = frozenset(
            user.groups.values_list("name", flat=True)
        )
    return user._ppm_role_names


def user_has_role(user, role):
    return role.value in get_user_roles(user)


def is_attendee(user):
    return user_has_role(user, Role.ATTENDEE)


def is_organizer(user):
    return user_has_role(user, Role.ORGANIZER)
