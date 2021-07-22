from django.shortcuts import render
from django.conf import settings
from django.db import connection
from .models import Node, Edge

import requests # for getting URL
import urllib # parsing url
import json # for parsing json
from time import sleep # rate limiting
import networkx as nx

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

    # Settings
    operator = 'vs' # adds this to each search query if it's not already there
    rate_limit = .05 # time between each query (seconds)
    n_bulk = 100 # bulk update size (100 max)

    # Variables
    clean_query = query.lower().strip()

    # Placeholders
    nodes_created = [0]
    bulk_edge_create = []
    bulk_edge_delete_ids = []

    # Data containers
    suggestion_history = {'all': []} # {all: ['a', 'b', 'c'], 1: ['a'], 2: ['b', 'c']} # sorted by relevance
    graph_nodes = {clean_query: {'value': 1, 'color': '#fdae6b'}} # {'a': 2} size of node
    graph_edges = [] # [{ 'from': 0, 'to': 1, 'value': 1250 }]

    #################################################
    # Functions

    # Check words to see if they're allowed
    def not_excluded(suggestion_word_split):
        # Exclude words
        exclude_words = [operator] # used to be 'vs', 'or', 'and'
        # If not blank
        if suggestion_word_split:
            # Not excluded words
            if not any(x in suggestion_word_split for x in exclude_words):
                # Not 1 character
                if not (len(suggestion_word_split) == 1 and len(suggestion_word_split[0]) == 1):
                    return True

    # Clean suggestion phrases to remove query (the query can sometimes change)
    def clean_suggestions(suggestion_list, relevance_list):
        results = {
            'suggestions': [],
            'relevance': [],
        }
        # For each suggestion
        for i, phrase in enumerate(suggestion_list):
            # Get relevance
            try:
                relevance = relevance_list[i]
            except:
                relevance = 0
            # Split words
            word_split = phrase.split()
            # Remove each word until you get to operator
            for word in phrase.split():
                word_split.remove(word)
                if word == operator.strip():
                    break
            # If the word isn't excluded
            if not_excluded(word_split):
                # Join words back into phrase and add to results
                results['suggestions'].append(' '.join(word_split))
                results['relevance'].append(relevance)
        # Return
        return results

    # Return google data
    def google_search(query):
        # Rate limit
        sleep(rate_limit)
        # Clean - lowercase and no whitespace
        query = query.lower().strip()
        # Clean - remove the operator if it's already there
        query = query if query[-len(operator):] != operator else query[:len(query) - len(operator)].strip()
        # Add operator back
        query_operator = f"{query} {operator}"
        # Google search
        url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query_operator)}'
        response_json = requests.request("GET", url).json()
        # Clean suggestions
        suggestion_list = response_json[1]
        relevance_list = response_json[4]['google:suggestrelevance'] if 'google:suggestrelevance' in response_json[4] else []
        cleaned_suggestions = clean_suggestions(suggestion_list, relevance_list)
        # Return data
        data = {
            'query': query,
            'query_operator': query_operator,
            'suggestions': cleaned_suggestions['suggestions'],
            'relevance': cleaned_suggestions['relevance'],
        }
        # Debug
        #settings.DEBUG and print(f"\n{response_json}\n\n{data}")
        return data

    # Make database updates
    def database_update(search_results):
        # If there are any search results
        if search_results['suggestions']:
            # Parent - get or create
            parent_obj, parent_created = Node.objects.get_or_create(name=search_results['query'])
            nodes_created[0] += 1 if parent_created else 0
            # Children - bulk create setup
            child_obj_relevance = []
            child_obj_ids = []
            for i, child in enumerate(search_results['suggestions']):
                child_obj, child_created = Node.objects.get_or_create(name=child)
                nodes_created[0] += 1 if child_created else 0
                child_obj_relevance.append([child_obj, search_results['relevance'][i]]) # [obj, 500]
                child_obj_ids.append(child_obj.id)
            # Children - If parent is new, create edges for all children
            if parent_created:
                for child_obj, relevance in child_obj_relevance: 
                    bulk_edge_create.append(Edge(
                        parent=parent_obj,
                        child=child_obj,
                        weight=relevance,
                    ))
            # Children - Else, parent not new - edges may be added or deleted
            else:
                # Get db list of parent's children
                db_edge_ids = Edge.objects.filter(parent=parent_obj).values_list('child', flat=True)
                # Check create - If current child not in children, create
                for child_obj, relevance in child_obj_relevance: 
                    if child_obj.id not in db_edge_ids:
                        bulk_edge_create.append(Edge(
                            parent=parent_obj,
                            child=child_obj,
                            weight=relevance,
                        ))
                # Check delete - if old child not in current children, delete
                for child_id in db_edge_ids:
                    if child_id not in child_obj_ids:
                        qs = Edge.objects.filter(parent=parent_obj, child_id=child_id)
                        if qs.exists():
                            bulk_edge_delete_ids.append(qs.first().id)
        # Else, no results / stub
        else:
            settings.DEBUG and print(f"* No search results - {search_results['query']}")
            
    # Update graph data
    def update_graph(search_results, color):
        # For each suggestion
        for i, suggestion in enumerate(search_results['suggestions']):
            # Add node
            if suggestion not in graph_nodes:
                graph_nodes[suggestion] = {
                    'value': 1,
                    'color': color,
                }
            else:
                graph_nodes[suggestion]['value'] += 1
            # Add edge
            weight = search_results['relevance'][i]
            graph_edges.append({
                'from': search_results['query'],
                'to': suggestion,
                'value': weight,
            })

    # Add suggestions to history (already sorted by relevance)
    def update_suggestion_history(search_results, level):
        # Add specific level
        if level in suggestion_history and isinstance(suggestion_history[level], list): 
            suggestion_history[level].extend(search_results['suggestions'])
        else:
            suggestion_history[level] = search_results['suggestions']
        # Add to all
        suggestion_history['all'].extend(search_results['suggestions'])

    #################################################
    # Google search, update database, update graph data

    # 1st level search
    search1 = google_search(query)
    database_update(search1)
    update_graph(search1, '#f3e24d')

    # Add to suggestion history
    update_suggestion_history(search1, 1)

    # For each child of 1st level (if it exists)
    if 1 in suggestion_history:
        for child1_query in suggestion_history[1]:

            # 2nd level search
            search2 = google_search(child1_query)
            database_update(search2)
            update_graph(search2, '#36c576') 

            # Add to suggestion history
            update_suggestion_history(search2, 2)

    # If there's not enough nodes
    if len(graph_nodes) <= 20:

        # For each child of 2nd level (if it exists)
        if 2 in suggestion_history:
            for child2_query in suggestion_history[2]:

                # 3rd level search
                search3 = google_search(child2_query)
                database_update(search3)
                update_graph(search3, '#2acdc0')

                # Add to suggestion history
                update_suggestion_history(search3, 3)

    # COLORS
    #c5493c
    #fdae6b
    #f3e24d
    #36c576
    #2acdc0
    #99c6c8
    #
    #6baed6
    #87d0af
    #0ca798

    #################################################
    # Edge - bulk actions

    # Bulk create
    if bulk_edge_create:
        Edge.objects.bulk_create(bulk_edge_create, batch_size=n_bulk, ignore_conflicts=True) # ignore errors

    # Bulk delete
    if bulk_edge_delete_ids:
        # Chunk deletions
        i_start = 0
        i_end = n_bulk
        while i_start < len(bulk_edge_delete_ids):
            Edge.objects.filter(id__in=bulk_edge_delete_ids[i_start:i_end]).delete()
            i_start = i_end
            i_end += n_bulk

    ########################################################
    # Form graph data

    # Placeholder
    graph_data = {
        'nodes': [],
        'edges': [],
    }

    # Edge combos
    edge_combos = {}

    # Add nodes
    node_list = list(graph_nodes.keys())
    for i, node in enumerate(node_list):
        graph_data['nodes'].append({
            'id': i,
            'value': graph_nodes[node]['value'],
            'label': node,
            'color': graph_nodes[node]['color'],
        })

    # Add edges
    for edge in graph_edges:
        # Get indices
        from_index = node_list.index(edge['from'])
        to_index = node_list.index(edge['to'])

        # From/To - Check if combo already exists (only show one line)
        if from_index in edge_combos:
            if to_index in edge_combos[from_index]:
                continue # skip loop
            else:
                edge_combos[from_index].append(to_index)
        else:
            edge_combos[from_index] = [to_index]

        # To/From - Check if combo already exists (only show one line)
        if to_index in edge_combos:
            if from_index in edge_combos[to_index]:
                continue # skip loop
            else:
                edge_combos[to_index].append(from_index)
        else:
            edge_combos[to_index] = [from_index]

        # Add edge
        graph_data['edges'].append({
            'from': from_index,
            'to': to_index,
            'value': edge['value'],
        })

    ########################################################
    # Networkx

    # Create edge list
    edgelist = [(node_list[e['from']], node_list[e['to']], e['value']) for e in graph_data['edges']] # [('a', 'b', 5.0), ('c', 'd', 7.3)]

    # Make graph
    G = nx.MultiDiGraph(edgelist)
    G2 = nx.Graph(G)

    # Communicability
    try:
        communicability = [(n, v) for n,v in nx.communicability(G2)[clean_query].items()]
        communicability.sort(key=lambda x:x[1])
        communicability.reverse()
    except:
        communicability = []

    # Communicability exp
    try:
        communicability_exp = [(n, v) for n,v in nx.communicability_exp(G2)[clean_query].items()]
        communicability_exp.sort(key=lambda x:x[1])
        communicability_exp.reverse()
    except:
        communicability_exp = []

    # Centrality
    centrality = [(n, v) for n,v in nx.degree_centrality(G).items()]
    centrality.sort(key=lambda x:x[1])
    centrality.reverse()

    ########################################################
    # Debug

    if settings.DEBUG:
        # Edge list
        print("-" * 100)
        print(edgelist)
        print("-" * 100)
        # Suggestion history
        print(f"* {len(suggestion_history) - 1} levels of search")
        for level, suggestions in suggestion_history.items():
            if level != 'all':
                print(f"> {level} - {suggestions}")
        # Database
        print("-" * 100)
        print(f"* Nodes - {nodes_created[0]} created")
        print(f"* Edges - {len(bulk_edge_create)} created, {len(bulk_edge_delete_ids)} deleted")
        print(f"* Database -  {len(connection.queries) if connection.queries else 0} queries")  
        # Networkx
        print("-" * 100)
        print(nx.info(G))
        # Rankings
        print("-" * 100)
        print("RANKINGS")
        google_ranking = []
        [google_ranking.append(x) for x in suggestion_history['all'] if x not in google_ranking and x != clean_query]
        print(f"* Google: {google_ranking[:10]}")
        print(f"* communicability: {[x[0] for x in communicability if x[0] != clean_query][:10]}")
        print(f"* communicability_exp: {[x[0] for x in communicability_exp if x[0] != clean_query][:10]}")
        print(f"* centrality: {[x[0] for x in centrality if x[0] != clean_query][:10]}")
        print(f"* voterank: {[x for x in nx.voterank(G) if x != clean_query][:10]}")
        # NOTES
            # Node-centered metrics are preferable because they take into account a starting point.
                # Google
                # Communicability
            # Graph-wide metrics can be really bad because they don't start at a specific node. 
            # So in a graph with many levels they can rank something far away from the initial query.
                # Centrality
                # Voterank 
        # Fin
        print("-" * 100)

    ########################################################

    # Render
    return render(request, 'search/result.html', context = {
        'input_value': clean_query,
        'graph_data': json.dumps(graph_data),
    })