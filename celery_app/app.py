from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=['celery_app.tasks']
)

celery_app.conf.timezone = 'UTC'
celery_app.conf.enable_utc = True

celery_app.conf.beat_schedule = {
    'get-dolar-price': {
        'task': 'celery_app.tasks.get_dolar_price',
        'schedule': crontab(minute='*/10'),
    },
    'process-not-extracted-cars': {
        'task': 'celery_app.tasks.process_not_extracted_cars',
        'schedule': crontab(hour='*/12'),
    },
    'process_extracted_cars': {
        'task': 'celery_app.tasks.process_extracted_cars',
        'schedule': crontab(minute='*/30'),
    }
}
