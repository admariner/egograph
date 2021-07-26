from django.shortcuts import render
from django.conf import settings

from core.classes.network import Network
from search.models import Edge
from search.classes.visjs import Visjs

import json # for parsing json
import networkx as nx # network analysis

#####################################################################################
# Network graph

def graph(request):

    # Make network obj
    network = Network()

    # Make visjs graph object
    visjs = Visjs(network.output_edgelist())

    # Debug
    if settings.DEBUG:
        network.print_debug(10)

    # Render
    return render(request, 'stats/graph.html', context = {
        'graph_data': json.dumps(visjs.output_graph_data()),
        'stats': visjs.output_network_stats(),
    })