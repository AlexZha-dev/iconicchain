from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class Organization(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    organization = models.ForeignKey(
        Organization, on_delete=models.PROTECT, related_name="users"
    )

    REQUIRED_FIELDS = [*AbstractUser.REQUIRED_FIELDS, "organization"]
    objects = UserManager()
