from .settings import *  # noqa: F403

# Tests do not need the local PostgreSQL service.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Password strength is covered by Django's production settings; fast hashing
# keeps API tests quick.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
