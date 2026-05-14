"""Celery initialization for Django project."""

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tweet_locator.settings')

app = Celery('tweet_locator')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')
