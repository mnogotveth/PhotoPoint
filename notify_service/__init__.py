from __future__ import absolute_import, unicode_literals

__all__ = ["celery_app"]

from .celery import app as celery_app  # noqa: E402,F401
