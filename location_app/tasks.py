"""Celery async tasks for location app."""

from celery import shared_task
from django.utils import timezone
from .models import LocationQuery


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def log_location_query(
    self,
    query_text: str,
    inferred_city: str | None,
    lat: float | None,
    lon: float | None,
    confidence: float | None,
    method: str = "semantic",
    keywords: list[str] | None = None,
):
    """
    Async task to log location queries without blocking the request.
    
    This runs in a separate worker process, so the HTTP response
    isn't delayed by database writes.
    """
    try:
        LocationQuery.objects.create(
            query_text=query_text,
            inferred_city=inferred_city,
            inferred_lat=lat,
            inferred_lon=lon,
            confidence=confidence,
            method=method,
            keywords_extracted=keywords or [],
        )
    except Exception as exc:
        # Retry on failure (with exponential backoff)
        raise self.retry(exc=exc)
