from django.conf import settings

from core.classes.network import Network
from stats.models import Stat
from stats.forceatlas2 import ForceAtlas2

from celery import shared_task
import networkx as nx

#####################################################################################
# Calculate x/y positions for network graph

@shared_task
def calc_network_graph_positions(nodes=5000, iterations=2000):

    # Make network object
    network = Network()

    # Make graphs
    G = nx.MultiDiGraph(network.output_edgelist_networkx())
    G2 = nx.Graph(G)

    ########################################################

    # Get sorted list of degree centrality
    degree_centrality_list = [(n, v) for n,v in nx.degree_centrality(G).items()]
    degree_centrality_list.sort(key=lambda x:x[1])
    degree_centrality_list.reverse()

    # Get largest subgraph sorted by degree
    largest_subgraph_nodes = max(nx.connected_components(G2), key=len) # {'a', 'b'}
    largest_subgraph_nodes_sorted_by_degree = [x[0] for x in degree_centrality_list if x[0] in largest_subgraph_nodes]

    # Make new graph object
    limited_subgraph = G.subgraph(largest_subgraph_nodes_sorted_by_degree[:nodes])

    # Make new edgelist
    edgelist_nx = []
    for from_node, to_node in nx.edges(limited_subgraph):
        edge_weight = G[from_node][to_node][0]['weight']
        edgelist_nx.append((from_node, to_node, {'weight': edge_weight}))

    ########################################################
    # Calculate positions

    forceatlas2 = ForceAtlas2(
        # Performance
        jitterTolerance = 1, # How much swinging you allow. Above 1 discouraged. Lower gives less speed and more precision
        barnesHutOptimize = True,
        barnesHutTheta = 1, # default 1.2. higher is faster but more simplistic
        # Tuning
        scalingRatio = 10, # default 2. How much repulsion you want. More makes a more sparse graph
        strongGravityMode = False, # A stronger gravity view
        gravity = 1, # default 1
        # Behavior alternatives
        outboundAttractionDistribution = True, # Dissuade hubs
        linLogMode = True, # Make graph circular
        adjustSizes = True, # Prevent overlap
        edgeWeightInfluence = 1, # How much influence you give to the edges weight. 0 is "no influence" and 1 is "normal"
        # Log
        verbose = settings.DEBUG,
    )

    # Calc positions
    G_new = nx.MultiDiGraph(edgelist_nx)
    positions = forceatlas2.forceatlas2_networkx_layout(G_new, iterations=iterations)

    # Save positions to database
    Stat.objects.update_or_create(
        name = 'positions',
        defaults = {'data': positions}
    )

    # Save edgelist to database
    Stat.objects.update_or_create(
        name = 'edgelist',
        defaults = {'data': edgelist_nx}
    )

    # Return
    return






    