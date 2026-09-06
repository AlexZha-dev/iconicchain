from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        if isinstance(extra_fields.get("organization"), (int, str)):
            if "organization_id" in extra_fields:
                raise ValueError("Pass organization or organization_id, not both.")
            extra_fields["organization_id"] = extra_fields.pop("organization")
        return super().create_superuser(username, email, password, **extra_fields)

    create_superuser.alters_data = True
