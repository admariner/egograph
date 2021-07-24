from django.urls import path

from . import views

app_name = 'export'
urlpatterns = [
    # Edgelist
    path('edgelist/', views.edgelist, name='edgelist'),
]