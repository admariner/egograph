from config.settings import *

################################################################################################

# CELERY
CELERY_BROKER_URL = os.environ['REDIS_URL']

# SECURITY
DEBUG = False # Should be False.
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['.egograph.com'] # A list of strings representing the host/domain names that this Django site can serve.
INTERNAL_IPS = type(str('c'), (), {'__contains__': lambda *a: True})() if DEBUG else [] # Allows debug variable in templates, accepts all IP addresses
