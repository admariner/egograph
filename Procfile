# NOTES
# Heroku automatically runs collectstatic

# Run project
web: gunicorn config.wsgi

# Celery worker to run tasks
worker: celery --app config worker

# Celery worker to run as scheduler
beat: celery --app config beat