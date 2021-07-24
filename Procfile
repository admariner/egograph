# NOTES
# Heroku automatically runs collectstatic

# Run project
web: gunicorn config.wsgi

# Celery worker to run periodic tasks
beat: celery --app config beat