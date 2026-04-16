import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'neorise_fsl.settings')

app = Celery('neorise_fsl')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
