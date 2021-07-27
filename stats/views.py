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

    # Get network edgelist
    network = Network()

    # Make graphs
    G = nx.MultiDiGraph(network.output_edgelist_networkx())
    G2 = nx.Graph(G)

    # Get sorted list of degree centrality
    degree_centrality_list = [(n, v) for n,v in nx.degree_centrality(G).items()]
    degree_centrality_list.sort(key=lambda x:x[1])
    degree_centrality_list.reverse()

    # Get largest subgraph sorted by degree
    largest_subgraph_nodes = max(nx.connected_components(G2), key=len) # {'a', 'b'}
    largest_subgraph_nodes_sorted_by_degree = [x[0] for x in degree_centrality_list if x[0] in largest_subgraph_nodes]

    # Make new graph object
    limit_to_n = 5000
    limited_subgraph = G.subgraph(largest_subgraph_nodes_sorted_by_degree[:limit_to_n])

    # Make new edgelist
    edgelist = []
    for from_node, to_node in nx.edges(limited_subgraph):
        edge_weight = G[from_node][to_node][0]['weight']
        edgelist.append((from_node, to_node, edge_weight))

    # IF NODES DON'T MATCH FINAL OUTPUT IT'S PROBABLY BECAUSE OF ISOLATES

    # Make visjs data
    visjs = Visjs(edgelist)
    visjs.calculate_graph_data()


    '''
    {
        id: 1,
        label: "Abdelmoumene Djabou",
        title: "Country: " + "Algeria" + "<br>" + "Team: " + "Club Africain",
        value: 22,
        group: 24,
        x: -1392.5499,
        y: 1124.1614,
    }
    '''

    # Debug
    if settings.DEBUG:
        print("-" * 100)
        print(nx.info(limited_subgraph))
        print("-" * 100)
        print(largest_subgraph_nodes_sorted_by_degree[:10])
        print("-" * 100)

    # Render
    return render(request, 'stats/graph.html', context = {
        'graph_data': json.dumps(visjs.output_graph_data()),
        'stats': visjs.output_network_stats(),
    })