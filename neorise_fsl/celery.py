import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neorise_fsl.settings')

app = Celery('neorise_fsl')
app.config_from_object('django.conf:settings', namespace='CELERY')
# autodiscover_tasks() only finds tasks.py per app. Phase 2 tasks live in
# generation/materials_tasks.py — register them explicitly.
app.autodiscover_tasks()
app.autodiscover_tasks(packages=['generation'], related_name='materials_tasks')
