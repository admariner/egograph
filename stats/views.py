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

    # Get edgelist (networkx format)
    try:
        edgelist_nx = Stat.objects.get(name='edgelist').data
    except:
        edgelist_nx = []

    # Get top nodes
    try:
        top_nodes = Stat.objects.get(name='top_nodes').data
    except:
        top_nodes = []

    # Get statistics
    try:
        statistics = Stat.objects.get(name='statistics').data
    except:
        statistics = []

    # Convert edgelist weights from dict to int
    edgelist_visjs = []
    for e in edgelist_nx:
        edgelist_visjs.append((e[0], e[1], e[2]['weight']))

    # IF NODES DON'T MATCH FINAL OUTPUT IT'S PROBABLY BECAUSE OF ISOLATES

    # Make visjs data
    visjs = Visjs(edgelist=edgelist_visjs, positions=positions)
    visjs.calculate_graph_data()

    # Debug
    if settings.DEBUG:
        print("-" * 100)
        print(nx.info(nx.MultiDiGraph(edgelist_nx)))
        print("-" * 100)

    # Render
    return render(request, 'stats/graph.html', context = {
        #
        'page_title': "Network Graph | EgoGraph",
        'page_desc': "Visualize the top nodes in the entire network graph.",
        #
        'graph_data': json.dumps(visjs.output_graph_data()),
        'top_nodes': top_nodes,
        'statistics': statistics,
    })
