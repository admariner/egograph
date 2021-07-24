from django.shortcuts import render
from django.conf import settings

from .models import Node, Edge
from .classes.search import Search

import json # for parsing json
import networkx as nx # network analysis

#####################################################################################
# Page - Landing

def landing(request):
    return render(request, 'search/landing.html', context = {
        'stats': {
            'nodes': Node.objects.count(),
            'edges': Edge.objects.count(),
        }
    })

#####################################################################################
# Page - Search Results

def result(request, query):

    # Clean query
    clean_query = query.lower().strip()

    # Make search object
    search = Search()

    #################################################
    # Google search, update database, update graph data

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

    # Perform db bulk create, update, delete
    settings.DEBUG and print("-" * 100)
    search.database_bulk_actions()
    settings.DEBUG and print("-" * 100)

    ########################################################
    # Create graph data

    # Keep parallel edges or collapse / average them together?
    keep_parallel_edges = True

    # Graph colors
    graph_colors = [
        '#fdae6b',
        '#f3e24d',
        '#36c576',
        '#2acdc0'
    ]

    # Data containers
    raw_edgelist = [] # [(from, to, value)]
    graph_node_dict = {clean_query: {'value': 1, 'color': graph_colors[0]}} # {'malbec': {'value': 9, 'color': 'hex'}
    graph_data = {
        'nodes': [], # [{'id': 1, 'label': 'x', 'value': 500, 'color': 'hex'}]
        'edges': [], # [{ 'from': 0, 'to': 1, 'value': 1250 }]
    }

    # Create node dict
    for from_node, to_results in search.search_history.items():
        # For each suggestion
        for i, to_node in enumerate(to_results['suggestions']):
            # If already added, update
            if to_node in graph_node_dict:
                graph_node_dict[to_node]['value'] += 1 # increases size of node
            # Else, add
            else:
                graph_node_dict[to_node] = {
                    'value': 1,
                    'color': graph_colors[to_results['level']],
                }
            # Add to edgelist
            value = to_results['weights'][i]
            raw_edgelist.append((from_node, to_node, value))

    # Make node list from node dict
    graph_node_list = list(graph_node_dict.keys())

    # Convert node dict to list
    for i, node in enumerate(graph_node_list):
        graph_data['nodes'].append({
            'id': i,
            'label': node,
            'value': graph_node_dict[node]['value'],
            'color': graph_node_dict[node]['color'],
        })

    # Edges - if we're keeping parallel edges, then simply add all
    if keep_parallel_edges:
        # Cycle through edge data
        for from_node, to_node, value in raw_edgelist:
            # Get indices
            from_index = graph_node_list.index(from_node)
            to_index = graph_node_list.index(to_node)
            # Add to graph
            graph_data['edges'].append({
                'from': from_index,
                'to': to_index,
                'value': value,
            })

    # Edges - else, we're collapsing / averaging parallel edges. 
    # Only one edge will be added for each parallel. Need to track all those created and average weights.
    else:
        # Data container
        edge_lookup = {} # {from_index: {to_index: [value]}
        # Cycle through edge data
        for from_node, to_node, value in raw_edgelist:
            # Get indices
            from_index = graph_node_list.index(from_node)
            to_index = graph_node_list.index(to_node)
            # 1) If from/to are not the same
            if from_index != to_index:
                # 2) Need to check if a from/to or to/from exists
                existing_edge_type = None # 'from_to' or 'to_from'
                if from_index in edge_lookup and to_index in edge_lookup[from_index]: # from/to
                    existing_edge_type = 'from_to'
                elif to_index in edge_lookup and from_index in edge_lookup[to_index]: # to/from
                    existing_edge_type = 'to_from'
                # 3) If nothing already exists, log new data
                if not existing_edge_type:
                    if from_index in edge_lookup:
                        edge_lookup[from_index][to_index] = [value]
                    else:
                        edge_lookup[from_index] = {to_index: [value]}
                # 4) Else, something exists, add value to that edge
                else:
                    if existing_edge_type == 'from_to':
                        edge_lookup[from_index][to_index].append(value)
                    elif existing_edge_type == 'to_from':
                        edge_lookup[to_index][from_index].append(value)
        # After all the data is organized, we can average and create edges
        for from_index, to_data in edge_lookup.items():
            for to_index, values in to_data.items():
                # Average and add
                graph_data['edges'].append({
                    'from': from_index,
                    'to': to_index,
                    'value': sum(values) / len(values),
                })

    ########################################################
    # Network_analysis

    # Get edge list - always use graph data so they match
    graph_edgelist = [(graph_node_list[e['from']], graph_node_list[e['to']], e['value']) for e in graph_data['edges']] # [(from, to, value)]

    # Make graph 
    G = nx.MultiDiGraph(graph_edgelist)
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
    # Rank google suggestions

    # Create list of all suggestions
    all_suggestions = []

    # Get a sorted list of the search history keys
    suggestion_history_keys = list(search.suggestion_history.keys())
    suggestion_history_keys.sort()

    # For each search level, add to the list
    for level in suggestion_history_keys:
        for s in search.suggestion_history[level]:
            all_suggestions.append(s)

    # Create ranked list of google suggestions
    google_suggestions_ranked = [] 
    [google_suggestions_ranked.append(s) for s in all_suggestions if s not in google_suggestions_ranked and s != clean_query]

    ########################################################
    # Debug

    if settings.DEBUG:
        # Suggestion history
        print(f"* {len(search.suggestion_history)} levels of search")
        print(f"> 0 - {[clean_query]}")
        for level, suggestions in search.suggestion_history.items():
            print(f"> {level} - {suggestions}")
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
        'graph_data': json.dumps(graph_data),
        'suggestions': {
            'google': google_suggestions_ranked[:n_rankings],
            'communicability': [x[0] for x in communicability_exp if x[0] != clean_query][:n_rankings]
        },
        'stats': {
            'nodes': G.number_of_nodes(),
            'edges': G.number_of_edges(),
        }
    })