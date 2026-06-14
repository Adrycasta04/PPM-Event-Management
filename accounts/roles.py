from enum import StrEnum


class Role(StrEnum):
    ATTENDEE = "Attendee"
    ORGANIZER = "Organizer"


def user_has_role(user, role):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=role.value).exists()


def is_attendee(user):
    return user_has_role(user, Role.ATTENDEE)


def is_organizer(user):
    return user_has_role(user, Role.ORGANIZER)
