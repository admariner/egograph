from search.models import Edge

import networkx as nx # network analysis
import csv # for saving csv

########################################################
# Networkx

class Graph:
    # Init
    def __init__(self):
        # Create edge list
        self.edgelist = list(Edge.objects.values_list('parent__name', 'child__name', 'weight'))
        # Make graphs
        self.G = nx.MultiDiGraph(self.edgelist)
        self.G2 = nx.Graph(self.G)

    # Saves edgelist as csv
    def save_edgelist(self):
        with open('edgelist.txt', 'w', newline='') as f:
            write = csv.writer(f, delimiter=' ')
            write.writerows(self.edgelist)

    # Prints network stats
    def stats(self, n_rankings):
        # Centrality - degree
        centrality_degree = [(n, v) for n,v in nx.degree_centrality(self.G).items()]
        centrality_degree.sort(key=lambda x:x[1])
        centrality_degree.reverse()
        # Print
        n_ljust = 20
        print(f"* {'Deg. centrality'.ljust(n_ljust)} - {[x[0] for x in centrality_degree][:n_rankings]}")
        print(f"* {'Voterank (undir)'.ljust(n_ljust)} - {[x for x in nx.voterank(self.G2)][:n_rankings]}")
