from config.settings import *

################################################################################################

# SECURITY
DEBUG = True # should be True (local only)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-5rz*dj5yn1)*nux&=_0-)bewcxb2=6v!ipecez^%32#rgv4y5(') # failover for local dev
ALLOWED_HOSTS = [] # When DEBUG is True and ALLOWED_HOSTS is empty, the host is validated against ['localhost', '127.0.0.1', '[::1]'].
INTERNAL_IPS = ['localhost', '127.0.0.1'] # Allows debug variable in templates, also needed for debug toolbar

# LOCAL DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'egograph',
        'USER': 'postgres',
        'PASSWORD': 'testing',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# DEBUG TOOLBAR
INSTALLED_APPS.append('debug_toolbar')
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware') # 0-indexed. Include as early as possible.
