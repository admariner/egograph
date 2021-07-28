from django.shortcuts import render

from search.models import Node, Edge

from django.db.models.functions import Trunc
from django.db.models import Count, Avg, F, ExpressionWrapper, fields

from datetime import datetime, timezone

#####################################################################################
# Page - Landing

def landing(request):

    # Formula for edge recency
    now = datetime.now(timezone.utc)
    days_since_children_updated = ExpressionWrapper(F('date_children_last_pulled') - now, output_field=fields.DurationField())

    # Nodes and edges
    nodes_data = list(Node.objects.annotate(day=Trunc('date_created', 'day')).values('day').annotate(total=Count('day'), completed=Count('date_children_last_pulled'), recency_avg=Avg(days_since_children_updated)).order_by('day'))
    edges_data = list(Edge.objects.annotate(day=Trunc('date_created', 'day')).values('day').annotate(total=Count('day')).order_by('day'))

    # Convert recency to days
    for n in nodes_data:
        if n['recency_avg']:
            n['recency_avg'] = abs(n['recency_avg'].total_seconds() / 60 / 60 / 24) # seconds to days

    # Return
    return render(request, 'core/landing.html', context = {
        'chart_data': {
            'nodes_data': nodes_data,
            'edges_data': edges_data
        }
    })
