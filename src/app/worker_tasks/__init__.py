from celery import Celery
import os 
# clr = Celery(
#     "tasks",
#     broker="redis://redis:6379/0",
#     backend="redis://redis:6379/0"
# )

# celery-broker if not in docker
if os.getenv('DOCKER') != 'true':
    clr = Celery(
        'tasks',
        broker='memory://',
        backend='rpc://'
    )
else:
    clr = Celery(
        'tasks',
        broker='redis://redis:6379/0',
        backend='redis://redis:6379/0'
    )