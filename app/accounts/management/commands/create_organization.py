from django.core.management.base import BaseCommand

from accounts.models import Organization


class Command(BaseCommand):
    help = "Create an organization, or show its ID if it already exists."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Organization name")

    def handle(self, *args, **options):
        organization, created = Organization.objects.get_or_create(name=options["name"])

        if created:
            message = f'Created organization "{organization.name}" (ID: {organization.pk}).'
        else:
            message = f'Organization "{organization.name}" already exists (ID: {organization.pk}).'

        self.stdout.write(self.style.SUCCESS(message))
