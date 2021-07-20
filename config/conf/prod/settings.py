from config.settings import *

################################################################################################

# SECURITY
DEBUG = False # Should be False.
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = ['.egograph.com'] # A list of strings representing the host/domain names that this Django site can serve.
INTERNAL_IPS = type(str('c'), (), {'__contains__': lambda *a: True})() if DEBUG else [] # Allows debug variable in templates, accepts all IP addresses

# SECURITY
SESSION_COOKIE_SECURE = True # If True, cookie is only sent with HTTPS
CSRF_COOKIE_SECURE = True # If True, cookie is only sent with HTTPS
SECURE_SSL_REDIRECT = True # If True, SecurityMiddleware redirects all non-HTTPS requests to HTTPS
X_FRAME_OPTIONS = 'DENY' # Default 'SAMEORIGIN', unless your site serves parts of itself in a frame, should be 'DENY'.