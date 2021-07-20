from django.contrib import admin
from django.urls import include, path
from django.conf import settings # for checking settings

import debug_toolbar

################################################################################################

urlpatterns = [
    # adsf
    path('', include('search.urls')),
    # Admin
    path('admin/', admin.site.urls),
]

################################################################################################
# DEBUG

if settings.DEBUG:
    # Debug toolbar
    urlpatterns.append( path('__debug__/', include(debug_toolbar.urls)) )
