from django.shortcuts import render
from django.conf import settings

from search.classes.search import Search 
from search.classes.visjs import Visjs

import json # for parsing json
import networkx as nx # network analysis

#####################################################################################
# Page - Search Results

def result(request, query):

    # Clean query
    clean_query = query.lower().strip()

    # Make search object
    search = Search()

    #################################################
    # Google search and udpate database

    # 1st level search
    search.google_and_prep_database(clean_query, 1)

    # For each child of 1st level (if it exists)
    if 1 in search.suggestion_history:
        for child1_query in search.suggestion_history[1]:

            # 2nd level search
            search.google_and_prep_database(child1_query, 2)

    # Make list of unique nodes
    unique_nodes = set()
    for level, suggestions in search.suggestion_history.items():
        for s in suggestions:
            unique_nodes.add(s)

    # If there's not enough nodes
    if len(unique_nodes) <= 15:

        # For each child of 2nd level (if it exists)
        if 2 in search.suggestion_history:
            for child2_query in search.suggestion_history[2]:

                # 3rd level search
                search.google_and_prep_database(child2_query, 3)

    # Perform db bulk actions
    settings.DEBUG and print("-" * 100)
    search.database_bulk_actions()

    # Calculate google suggestions
    google_suggestions_ranked = search.output_google_rankings()

    ########################################################
    # Network_analysis

    # Make visjs graph object from search data
    visjs = Visjs(search.output_edgelist(), clean_query)

    # Make nx object from graph data
    G = nx.MultiDiGraph(visjs.output_edgelist())
    G2 = nx.Graph(G)

    # Communicability exp
    try:
        communicability_exp = [(n, v) for n,v in nx.communicability_exp(G2)[clean_query].items()]
        communicability_exp.sort(key=lambda x:x[1])
        communicability_exp.reverse()
    except:
        communicability_exp = []

    # Communicability
    try:
        communicability = [(n, v) for n,v in nx.communicability(G2)[clean_query].items()]
        communicability.sort(key=lambda x:x[1])
        communicability.reverse()
    except:
        communicability = []

    # Centrality - degree
    centrality_degree = [(n, v) for n,v in nx.degree_centrality(G).items()]
    centrality_degree.sort(key=lambda x:x[1])
    centrality_degree.reverse()

    ########################################################
    # Debug

    # Output
    if settings.DEBUG:
        # Output search debug
        print("-" * 100)
        search.output_debug()
        print("-" * 100)
        # Networkx
        print(nx.info(G))
        print("-" * 100)
        # Rankings
        n_rankings = 5
        n_ljust = 25
        print("RANKINGS")
        print(f"* {'Google autocomplete'.ljust(n_ljust)} - {google_suggestions_ranked[:n_rankings]}")
        print(f"* {'Communicability (exp)'.ljust(n_ljust)} - {[x[0] for x in communicability_exp if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Communicability'.ljust(n_ljust)} - {[x[0] for x in communicability if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Deg. centrality'.ljust(n_ljust)} - {[x[0] for x in centrality_degree if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Voterank (undir)'.ljust(n_ljust)} - {[x for x in nx.voterank(G2) if x != clean_query][:n_rankings]}")
        print("-" * 100)
        # NOTES
            # Node-centered metrics are preferable because they take into account a starting point.
                # Google - ???
                # Communicability - starting at a node, how many walks end up at other nodes
            # Graph-wide metrics don't start at a specific node. So in a graph with many levels they can rank something far from the initial query.
                # Degree centrality
                    # Sorted by the fraction of nodes each is connected to.
                    # Takes into account 2nd-level networks more. So will pick nodes with strong 2nd-level neighors, even if 1st-level is small.
                # Voterank
                    # Each node votes for its neighbors through a series of rounds.
                    # Doesn't take into account 2nd-level networks. So it could discount nodes with influential neighbors.

    ########################################################
    # Render

    # Number of rankings to show on results
    n_rankings = 10

    # Render
    return render(request, 'search/result.html', context = {
        'input_value': clean_query,
        'graph_data': json.dumps(visjs.output_graph_data()),
        'suggestions': {
            'google': google_suggestions_ranked[:n_rankings],
            'communicability': [x[0] for x in communicability_exp if x[0] != clean_query][:n_rankings]
        },
        'stats': visjs.output_network_stats()
    })