from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),
]