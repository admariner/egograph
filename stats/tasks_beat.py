from celery import shared_task

from core.classes.network import Network
from stats.models import Stat
from stats.forceatlas2 import ForceAtlas2

import networkx as nx

#####################################################################################
# Calculate x/y positions for network graph

@shared_task
def calc_network_graph_positions(nodes_to_calc=10000):

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
    limit_to_n = nodes_to_calc
    limited_subgraph = G.subgraph(largest_subgraph_nodes_sorted_by_degree[:limit_to_n])

    # Make new edgelist
    edgelist_new = []
    for from_node, to_node in nx.edges(limited_subgraph):
        edge_weight = G[from_node][to_node][0]['weight']
        edgelist_new.append((from_node, to_node, edge_weight))

    ########################################################
    # Calculate positions

    forceatlas2 = ForceAtlas2(
        # Performance
        jitterTolerance = 1, # How much swinging you allow. Above 1 discouraged. Lower gives less speed and more precision
        barnesHutOptimize = True,
        barnesHutTheta = 1.2, # default 1.2. higher is faster but more simplistic
        # Tuning
        scalingRatio = 1, # default 2. How much repulsion you want. More makes a more sparse graph
        strongGravityMode = False, # A stronger gravity view
        gravity = 1, # default 1
        # Behavior alternatives
        outboundAttractionDistribution = True, # Dissuade hubs
        linLogMode = True, # Make graph circular
        adjustSizes = False, # Prevent overlap
        edgeWeightInfluence = 1, # How much influence you give to the edges weight. 0 is "no influence" and 1 is "normal"
        # Log
        verbose=True,
    )

    # Calc positions
    G_new = nx.MultiDiGraph(edgelist_new)
    positions = forceatlas2.forceatlas2_networkx_layout(G_new, iterations=1000)

    # Save positions to database
    try:
        stat_obj = Stat.objects.get(name='positions')
        stat_obj.data = positions
        stat_obj.save()
    except:
        Stat.objects.create(name='positions', data=positions)

    # Return
    return






    