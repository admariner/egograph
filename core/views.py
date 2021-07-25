from django.shortcuts import render

from search.models import Node, Edge

#####################################################################################
# Page - Landing

def landing(request):
    return render(request, 'core/landing.html', context = {
        'stats': {
            'nodes': Node.objects.count(),
            'edges': Edge.objects.count(),
        }
    })
