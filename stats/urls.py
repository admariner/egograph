from django.urls import path

from . import views

app_name = 'stats'
urlpatterns = [
    # Draw entire network graph
    path('graph/', views.graph, name='graph'),  
]