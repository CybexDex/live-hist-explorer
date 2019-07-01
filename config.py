import os
MONGODB_DB_URL = os.environ.get('MONGO_WRAPPER', "mongodb://yoyo:yoyo123@127.0.0.1:27017/cybex") # clockwork
MONGODB_DB_NAME = os.environ.get('MONGO_DB_NAME', 'cybex')
# Cache: see https://flask-caching.readthedocs.io/en/latest/#configuring-flask-caching
Name= 'live-hist'
CELERY_BROKER_URL='redis://localhost:6379/0'
CELERY_RESULT_BACKEND='redis://localhost:6379/0'
TODIR='/tmp/livespace/'

MAIL_SERVER='smtp.qq.com'
MAIL_PORT='465'
MAIL_USERNAME='313548025@qq.com'
MAIL_PASSWORD='ooutzpttcmkrbgce'
MAIL_DEFAULT_SENDER='313548025@qq.com'
