from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.roles import Role


class Command(BaseCommand):
    help = "Create the Attendee and Organizer groups."

    def handle(self, *args, **options):
        created_groups = []

        for role in Role:
            _, created = Group.objects.get_or_create(name=role.value)
            if created:
                created_groups.append(role.value)

        if created_groups:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created groups: {', '.join(created_groups)}."
                )
            )
        else:
            self.stdout.write("Role groups already exist.")
