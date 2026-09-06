FROM python:3.14-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==2.4.1"

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --with dev --no-root

COPY app ./app

RUN groupadd --system app \
    && useradd --system --gid app app \
    && mkdir -p app/media app/staticfiles \
    && DJANGO_ENVIRONMENT=development \
       DJANGO_SECRET_KEY=build-only-not-a-runtime-secret \
       POSTGRES_DB=unused \
       POSTGRES_USER=unused \
       POSTGRES_PASSWORD=unused \
       POSTGRES_HOST=unused \
       python app/manage.py collectstatic --noinput \
    && chown -R app:app /code

USER app

EXPOSE 8000

CMD ["gunicorn", "--chdir", "app", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
