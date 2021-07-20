from django.urls import path

from . import views

app_name = 'search'
urlpatterns = [
    # Landing
    path('', views.landing, name='landing'),
    # Search results
    path('graph/<path:query>/', views.result, name='result'),  
]