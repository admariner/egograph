from django.shortcuts import render

from search.models import Node, Edge

#####################################################################################
# Page - Landing

def landing(request):
    return render(request, 'core/landing.html', context = {
        'stats': {
            'Nodes': Node.objects.count(),
            'Edges': Edge.objects.count(),
        }
    })
