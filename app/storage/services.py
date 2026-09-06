import logging

from django.db import transaction

from .models import StoredFile

logger = logging.getLogger(__name__)


def save_upload(**validated_data):
    instance = StoredFile(**validated_data)
    uploaded_file = instance.file
    instance.file.save(uploaded_file.name, uploaded_file.file, save=False)
    try:
        with transaction.atomic():
            instance.save(force_insert=True)
    except Exception:
        try:
            instance.file.storage.delete(instance.file.name)
        except Exception:
            logger.exception(
                "Could not remove an uncommitted upload: %s", instance.file.name
            )
        raise
    return instance
