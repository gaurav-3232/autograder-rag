from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    'autograder',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.worker.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'app.worker.tasks.grade_submission': {'queue': 'grading'}
    }
)

from app.worker import tasks  # noqa: F401, E402