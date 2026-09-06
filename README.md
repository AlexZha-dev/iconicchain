# Django Storage App

A small Django application for uploading files, protected downloads, and download audit records. The API uses Django REST Framework session authentication and is available through the browsable API.

## Features

- Users belong to organizations through the custom `accounts.User` model.
- Each upload request accepts exactly one file. The server determines the author, organization, original filename, and file size.
- Files are stored under UUID-based paths rather than client-supplied filenames.
- Downloads go through an authenticated API endpoint and create a `Download` record for every `GET` request.
- Django admin shows files and download records as read-only and never exposes a direct public `media` URL.
- PostgreSQL runs in Docker Compose; WhiteNoise serves static files.

## Quick start with Docker

Docker Desktop with Docker Compose is required.

Create `.env` without overwriting an existing file:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

`.env.example` already contains the non-secret local Compose values. In `.env`, set `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`. Run the following command twice and use a different result for each value:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

The complete `.env.example` template is:

```dotenv
DJANGO_ENVIRONMENT=development
DJANGO_SECRET_KEY=<generated-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_HTTPS=False
DJANGO_TRUST_PROXY_SSL_HEADER=False
DJANGO_HSTS_SECONDS=0

POSTGRES_DB=file_storage
POSTGRES_USER=file_storage
POSTGRES_PASSWORD=<generated-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_EXPOSED_PORT=5433

MAX_UPLOAD_SIZE=52428800
```

`.env` contains secrets and must not be committed to Git.

Build and start the services, then apply the committed migrations:

```powershell
docker compose up --build -d
docker compose exec web python app/manage.py migrate
```

The application is available at <http://localhost:8000/>.

## First administrator

A superuser must belong to an organization. Create an organization first and note the printed ID:

```powershell
docker compose exec web python app/manage.py create_organization Acme
```

The command prints a message such as `Created organization "Acme" (ID: 1).` Running it again with the same name does not create a duplicate; it prints the ID of the existing organization instead. Quote names containing spaces:

```powershell
docker compose exec web python app/manage.py create_organization "Acme Ltd"
```

Then create an administrator:

```powershell
docker compose exec web python app/manage.py createsuperuser
```

When prompted for the organization, enter its ID. The admin is available at <http://localhost:8000/admin/>.

## API and login

Log in at <http://localhost:8000/api-auth/login/>, then open <http://localhost:8000/api/>.

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `/api/` | API entry point |
| `GET` | `/api/files/` | List files with authors, organizations, and download counts |
| `POST` | `/api/files/` | Upload one `multipart/form-data` file in the `file` field |
| `GET` | `/api/files/<id>/download/` | Download a file and record the download event |
| `GET` | `/api/files/<id>/downloads/` | List a file's download history |
| `GET` | `/api/organizations/` | List organizations and download counts for their files |
| `GET` | `/api/users/<id>/downloads/` | List a user's download history |

All API endpoints require authentication. Regular users do not need `is_staff=True`; that flag is required only for Django admin.

### Important access boundary

Storage is currently shared: every authenticated user can view the API file and audit lists and can download a file by a known ID. An organization is recorded during upload but is not yet used to filter results. To isolate organizations, add object-level permissions and filter querysets by `request.user.organization`.

## Uploads and storage

- The maximum size of one file is `MAX_UPLOAD_SIZE`, 50 MiB by default.
- Django limits multipart requests to one file.
- `media` is not served as a public URL; `MEDIA_URL` is only a technical prefix.
- `GET` requests to the download endpoint create `Download` records; `HEAD` requests do not.
- A `Download` record means that a download response was prepared. It does not guarantee the client received the complete stream.

The serializer's file-size validation does not replace a request-body size limit at an external reverse proxy.

## Tests

Install the development dependency group:

```powershell
poetry install --with dev
```

Run all tests:

```powershell
poetry run pytest
```

Run only the storage API tests:

```powershell
poetry run pytest app/storage/tests.py
```

`config.test_settings` uses in-memory SQLite and the fast MD5 password hasher only for tests. The application configuration continues to use PostgreSQL and Argon2.

## Local development without Docker

After installing dependencies and filling in `.env`, Django commands can be run directly:

```powershell
poetry run python app/manage.py migrate
poetry run python app/manage.py runserver
```

Create an organization in this mode with the same command, without Docker:

```powershell
poetry run python app/manage.py create_organization Acme
```

For this mode, `POSTGRES_HOST` must point to an accessible local PostgreSQL server, such as `localhost`, rather than the Compose service `db`.

## Security and operation

- Create passwords with `create_user`, `createsuperuser`, admin, or `set_password`; never assign the `password` field directly.
- Passwords use Argon2. Sessions use `HttpOnly`, `SameSite=Lax`, and a 3600-second lifetime.
- HTTPS, secure cookies, and redirects are controlled by `DJANGO_HTTPS`. It must be `False` for local HTTP.
- In production, `DJANGO_ENVIRONMENT=production` requires debug to be disabled, HTTPS enabled, a strong secret, and explicit host names without wildcards.
- Organization, user, file, and download-event relationships use `PROTECT` so accidental deletion does not erase history. This does not replace a separate retention, anonymization, or file-byte deletion policy.
