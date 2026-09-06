from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from .models import Organization


class CreateOrganizationCommandTests(TestCase):
    def test_creates_an_organization_only_once(self):
        output = StringIO()

        call_command("create_organization", "Acme", stdout=output)
        call_command("create_organization", "Acme", stdout=output)

        self.assertEqual(Organization.objects.filter(name="Acme").count(), 1)
        self.assertIn("Created organization", output.getvalue())
        self.assertIn("already exists", output.getvalue())
