from django.contrib import admin
from django.urls import include, path
from django.conf import settings # for checking settings

import debug_toolbar

################################################################################################

urlpatterns = [
    # Apps
    path('', include('core.urls')),
    path('search/', include('search.urls')),
    path('stats/', include('stats.urls')),
    path('export/', include('export.urls')),
    # Admin
    path('admin/', admin.site.urls),
]

################################################################################################
# DEBUG

if settings.DEBUG:
    # Debug toolbar
    urlpatterns.append( path('__debug__/', include(debug_toolbar.urls)) )
