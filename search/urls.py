from django.urls import path

from . import views

app_name = 'search'
urlpatterns = [
    # Search results
    path('search/<path:query>/', views.result, name='result'),  
]