from celery import Celery

import config
celery = Celery(config.Name, broker=config.CELERY_BROKER_URL)

