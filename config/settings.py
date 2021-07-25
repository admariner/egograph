import os

from celery.schedules import crontab # celery beat
import django_heroku
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

################################################################################################
# DJANGO SETTINGS

# Build paths inside the project like this. 
# Changes depending on where settings file is.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, 'content')

# This is where django discovers the different modules that are part of your project.
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic', # To use whitenoise in development. Put at top to disable Django DEV static handling
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
        # humanize
    'django.contrib.staticfiles',
        # sites
        # sitemaps
    # Custom apps
    'core',
    'search',
    'stats',
    'export',
]

# Every time a request hits the Django server it runs through the middleware.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # 3rd party - serves static files in PROD
    'django.contrib.sessions.middleware.SessionMiddleware', # Django - manages sessions across requests.
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Django - associates users with requests using sessions.
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(CONTENT_DIR, 'templates')], # serve from the content folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    }, {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True # enable Django’s translation system
USE_L10N = True # enable localized translation of data 
USE_TZ = True # make datetimes timezone aware

# Messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

# SENTRY
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', None), # No logging for local dev
    integrations=[DjangoIntegration(), RedisIntegration()],
    send_default_pii=True, # add user info to errors
    #debug=True, # logs sentry info to console
)

################################################################################################
# CELERY SCHEDULER
# https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html

CELERY_BEAT_SCHEDULE = {
    # Core - delete nodes without edges
    'delete_nodes_without_edges': { 
        'task': 'core.tasks_beat.delete_nodes_without_edges', 
        'schedule': crontab(minute=0, hour=0), # Execute daily at midnight
    },
    # Search - pull children for nodes that haven't done so yet
    'pull_children_for_nodes_without_them': { 
        'task': 'search.tasks_beat.pull_children_for_nodes_without_them', 
        'schedule': crontab(minute='*/1'), # Execute every minute
    },
}

################################################################################################
# STATIC FILES - served from heroku using django-whitenoise

# STATIC
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') # Path where collectstatic will collect static files for deployment.
STATIC_URL = '/static/' # URL to use when referring to static files located in STATIC_ROOT.

# Where to find static files on server
STATICFILES_DIRS = [
    os.path.join(CONTENT_DIR, 'static'),
]

# Whitenoise compression/caching support
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' 

################################################################################################
# ENV-SPECIFIC SETTINGS

# Set in Heroku
IS_PRODUCTION = os.environ.get('IS_PRODUCTION')

# Load different settings based on environment
if IS_PRODUCTION:
    from .conf.prod.settings import * # Heroku prod
else:
    from .conf.dev.settings import * # Local dev

################################################################################################
# HEROKU

django_heroku.settings(locals())