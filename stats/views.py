from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse

from core.classes.network import Network
from search.classes.visjs import Visjs
from stats.models import Stat

from .forceatlas2 import ForceAtlas2
import json # for parsing json
import networkx as nx # network analysis

#####################################################################################
# Network graph

def graph(request):

    # Get positions
    try:
        positions = Stat.objects.get(name='positions').data
    except:
        positions = {}

    # Get network obj
    network = Network()

    # Make subgraph
    G = nx.MultiDiGraph(network.output_edgelist_networkx())
    subgraph = G.subgraph(positions.keys())

    # Make new edgelist
    edgelist_new = []
    for from_node, to_node in nx.edges(subgraph):
        edge_weight = G[from_node][to_node][0]['weight']
        edgelist_new.append((from_node, to_node, edge_weight))

    ########################################################

    # IF NODES DON'T MATCH FINAL OUTPUT IT'S PROBABLY BECAUSE OF ISOLATES

    # Make visjs data
    visjs = Visjs(edgelist=edgelist_new, positions=positions)
    visjs.calculate_graph_data()

    # Debug
    if settings.DEBUG:
        print("-" * 100)
        print(nx.info(subgraph))
        print("-" * 100)

    # Render
    return render(request, 'stats/graph.html', context = {
        'page_title': "Network Graph | EgoGraph",
        'page_desc': "Visualize the top nodes in the entire network graph.",
        #
        'graph_data': json.dumps(visjs.output_graph_data()),
        'stats': visjs.output_network_stats(),
    })
