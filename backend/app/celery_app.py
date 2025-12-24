"""
Celery application configuration for background tasks
"""

from celery import Celery
from app import create_app

def make_celery(app=None):
    """Create and configure Celery application."""
    if app is None:
        app = create_app()
    
    celery = Celery(
        app.import_name,
        backend=app.config['REDIS_URL'],
        broker=app.config['REDIS_URL']
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        worker_prefetch_multiplier=1,
    )
    
    class ContextTask(celery.Task):
        """Task that runs within Flask application context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    return celery

# Create celery app instance
flask_app = create_app()
celery_app = make_celery(flask_app)


# Import tasks to register them
# from app.tasks import *
