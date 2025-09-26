# Fichier: app/worker.py

from celery import Celery
from core.config import settings

# Crée l'instance de l'application Celery
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery pour qu'il découvre automatiquement les tâches
# dans les fichiers nommés 'tasks.py' de notre projet.
celery_app.autodiscover_tasks(['core'])