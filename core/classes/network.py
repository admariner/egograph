from django.conf import settings
from django.db import connection

from search.models import Node, Edge

import networkx as nx
import csv

#####################################################################################
# Network class

class Network:
    "Class that handles interactions with the network data"

    #################################################
    # Variables

    # Init
    def __init__(self):
        pass

    #################################################
    # External functions 

    # Output and optionally delete nodes without edges
    def nodes_without_edges(self, delete=False):
        'Counts nodes that no longer have any edges and can delete them.'

        # Create node/edge sets
        node_set = set(Node.objects.values_list('id', flat=True))
        edge_set = set(Edge.objects.values_list('parent_id', flat=True)).union(set(Edge.objects.values_list('child_id', flat=True)))

        # Create list of nodes without edges
        nodes_without_edges = list(node_set - edge_set)

        # Delete by id
        if delete:
            # Settings
            n_bulk = 100
            # Chunk deletions
            i_start = 0
            i_end = n_bulk
            while i_start < len(nodes_without_edges):
                Node.objects.filter(id__in=nodes_without_edges[i_start:i_end]).delete()
                i_start = i_end
                i_end += n_bulk
 
        # Return
        return len(nodes_without_edges)

    # Output edgelist [(from, to, weight)]
    def output_edgelist(self):
        return list(Edge.objects.values_list('parent__name', 'child__name', 'weight'))

    # Output edgelist in networkx format [(from, to, {'weight': 500})]
    def output_edgelist_networkx(self):
        edgelist = []
        data = list(Edge.objects.values_list('parent__name', 'child__name', 'weight'))
        for from_node, to_node, weight in data:
            edgelist.append((from_node, to_node, {'weight': weight}))
        return edgelist

    # Write edgelist to file
    def write_edgelist_to_file(self, file_obj, delimiter=" "):
        # Make writer
        writer = csv.writer(file_obj, delimiter=delimiter)
        # Write headers
        writer.writerow(["Source", "Target", "Weight"])
        # Clean text function. Turns "e k" into "e_k"
        def clean_name(name):
            temp = name.split()
            return "_".join(temp)
        # Write rows
        for parent, child, value in self.output_edgelist():
            writer.writerow([clean_name(parent), clean_name(child), value])

    # Import edgelist to database from file
    def import_edgelist_from_file(self, file_path, delimiter=" ", debug=settings.DEBUG):

        # Data containers
        bulk_edge_create = []
        node_obj_dict = []

        # Open file
        edgelist = []
        with open(file_path, encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            next(reader) # Skip header
            for row in reader:
                edgelist.append(tuple(row))

        # Debug
        debug and print(f"{len(edgelist)} edges to import.")

        # Nodes - get objects
        for row in edgelist:
            # Get info
            from_name = row[0].replace('_', ' ')
            to_name = row[1].replace('_', ' ')
            weight = row[2]
            # Get objects - From
            if from_name in node_obj_dict:
                from_obj = node_obj_dict[from_name]
            else:
                from_obj, from_created = Node.objects.get_or_create(name=from_name)
                node_obj_dict[from_name] = from_obj
            # Get objects - To
            if to_name in node_obj_dict:
                to_obj = node_obj_dict[to_name]
            else:
                to_obj, from_created = Node.objects.get_or_create(name=to_name)
                node_obj_dict[to_name] = to_obj
            # Add edge to bulk
            bulk_edge_create.append(Edge(
                parent=from_obj,
                child=to_obj,
                weight=weight,
            ))

        # Edges - bulk create
        if bulk_edge_create:
            n_bulk = 100
            Edge.objects.bulk_create(bulk_edge_create, batch_size=n_bulk, ignore_conflicts=True) # ignore errors

        # Debug
        if debug: 
            print(f"* Edges - {len(bulk_edge_create)} created")
            print(f"* Database -  {len(connection.queries) if connection.queries else 0} queries") 

    # Prints network stats and debug
    def print_debug(self, n_rankings=10):
        # Make graphs
        G = nx.MultiDiGraph(self.output_edgelist_networkx())
        G2 = nx.Graph(G)
        # Centrality - degree
        centrality_degree = [(n, v) for n,v in nx.degree_centrality(G).items()]
        centrality_degree.sort(key=lambda x:x[1])
        centrality_degree.reverse()
        # PRINT
        # Meta
        print("-" * 100)
        print(nx.info(G))
        print("-" * 100)
        # Rankings
        n_ljust = 25
        print("RANKINGS")
        print(f"* {'Deg. centrality'.ljust(n_ljust)} - {[x[0] for x in centrality_degree][:n_rankings]}")
        print(f"* {'Voterank (undir)'.ljust(n_ljust)} - {[x for x in nx.voterank(G2)][:n_rankings]}")
        print("-" * 100)







# https://cambridge-intelligence.com/keylines-faqs-social-network-analysis/

# Degree Centrality - won't help much because all nodes have similar amount of children
# Betweenness centrality
# Closeness centrality
# EigenCentrality
# PageRank