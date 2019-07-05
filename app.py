import connexion,config

options = {'swagger_url': '/apidocs'}
app = connexion.FlaskApp('live-hist', options=options)

from flask_cors import CORS
CORS(app.app)

# from services.cache import cache
# cache.init_app(app.app)

app.add_api('api.yaml')
# import services.profiler
# services.profiler.init_app(app.app)
from services.cache import cache
cache.init_app(app.app)

from services.celery import celery
app.app.config['CELERY_BROKER_URL'] = config.CELERY_BROKER_URL
app.app.config['CELERY_RESULT_BACKEND'] =  config.CELERY_RESULT_BACKEND
celery.conf.update(app.app.config)

application = app.app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port = 8082, use_reloader=True)


