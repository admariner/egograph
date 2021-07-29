from django.conf import settings

from core.classes.network import Network
from stats.models import Stat
from stats.forceatlas2 import ForceAtlas2

from celery import shared_task
import networkx as nx

#####################################################################################
# Calculate x/y positions for network graph

@shared_task
def calc_network_graph_data(nodes=5000, iterations=2000):

    # Make network object
    network = Network()

    # Make graphs
    G_dir = nx.MultiDiGraph(network.output_edgelist_networkx())
    G_undir = nx.Graph(G_dir)

    # Get sorted list of degree centrality
    degree_centrality_list = [(n, v) for n,v in nx.degree_centrality(G_dir).items()] # diffrent if you pick undirected
    degree_centrality_list.sort(key=lambda x:x[1])
    degree_centrality_list.reverse()

    # Get largest connected components
    largest_cc_nodes = max(nx.connected_components(G_undir), key=len) # must be undirected
    largest_cc_nodes_sorted_by_degree = [x[0] for x in degree_centrality_list if x[0] in largest_cc_nodes]

    # Make largest subgraphs
    subgraph_G_dir = G_dir.subgraph(largest_cc_nodes)
    subgraph_G_undir = G_undir.subgraph(largest_cc_nodes)

    ########################################################
    # Calculate top nodes and statistics

    # Top nodes by degree centrality - the fraction of nodes it is connected to.
    top_nodes = [x[0] for x in degree_centrality_list][:20]

    # Statistics
    statistics = [
        ('Nodes', subgraph_G_dir.number_of_nodes()),
        ('Edges', subgraph_G_dir.number_of_edges()), # diffrent if you pick undirected
        ('Clustering', f"{nx.average_clustering(subgraph_G_undir):2.1%}"), # must be undirected
        ('Transitivity', f"{nx.transitivity(subgraph_G_undir):2.1%}"), # must be undirected
    ]

    ########################################################
    # Make subgraph with limited nodes

    # Make limited subgrpah. When you do this you may introduce isolates so you need another subgraph after.
    lim_subgraph_temp = G_undir.subgraph(largest_cc_nodes_sorted_by_degree[:nodes])
    lim_subgraph_nodes = max(nx.connected_components(lim_subgraph_temp), key=len) # must be undirected
    lim_subgraph_G_dir = G_dir.subgraph(lim_subgraph_nodes)

    # Make new edgelist
    edgelist_nx = []
    for from_node, to_node in nx.edges(lim_subgraph_G_dir):
        edge_weight = G_dir[from_node][to_node][0]['weight']
        edgelist_nx.append((from_node, to_node, {'weight': edge_weight}))

    ########################################################
    # Debug

    if settings.DEBUG:
        print(nx.info(lim_subgraph_G_dir))
        print(statistics)
        print(top_nodes)

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
    positions = forceatlas2.forceatlas2_networkx_layout(lim_subgraph_G_dir, iterations=iterations)

    ########################################################
    # Update database

    # Positions
    Stat.objects.update_or_create(
        name = 'positions',
        defaults = {'data': positions}
    )

    # Edgelist
    Stat.objects.update_or_create(
        name = 'edgelist',
        defaults = {'data': edgelist_nx}
    )

    # Top nodes
    Stat.objects.update_or_create(
        name = 'top_nodes',
        defaults = {'data': top_nodes}
    )

    # Statistics
    Stat.objects.update_or_create(
        name = 'statistics',
        defaults = {'data': statistics}
    )

    # Return
    return






    