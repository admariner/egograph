from django.shortcuts import render
from django.conf import settings
from django.db import connection
from .models import Node, Edge

import requests # for getting URL
import urllib # parsing url
import json # for parsing json
from time import sleep # rate limiting
import networkx as nx # network analysis
from datetime import datetime, timezone, timedelta # for getting time

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
    dt_now = datetime.now(timezone.utc)
    dt_30_days_ago = dt_now - timedelta(days=30)

    # Bulk containers
    bulk_edge_create = []
    bulk_edge_update_weight = []
    bulk_edge_delete_ids = []

    # Data containers
    nodes_created = [0]
    node_query_obj_dict = {} # {'blueberry': (node_obj, node_created)}
    suggestion_history = {'all': []} # {all: ['a', 'b', 'c'], 1: ['a'], 2: ['b', 'c']} # sorted by weight
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
    def clean_suggestions(suggestion_list, weight_list):
        results = {
            'suggestions': [],
            'weights': [],
        }
        # For each suggestion
        for i, phrase in enumerate(suggestion_list):
            # Get weight
            try:
                weight = weight_list[i]
            except:
                weight = 0
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
                results['weights'].append(weight)
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
        # Node object - if already stored, get
        if query in node_query_obj_dict:
            node_obj, node_created = node_query_obj_dict[query]
        # Node object - else, hasn't been stored
        else:
            # Get/create
            node_obj, node_created = Node.objects.get_or_create(name=query)
            nodes_created[0] += 1 if node_created else 0
            # Store data
            node_query_obj_dict[query] = (node_obj, node_created)
        # Check if this query has recently been pulled in the database
        node_recently_pulled = False
        if node_obj.date_children_last_pulled and dt_30_days_ago:
            node_recently_pulled = node_obj.date_children_last_pulled >= dt_30_days_ago
        # If node recently pulled
        if node_recently_pulled:
            # Debug
            settings.DEBUG and print(f"* Recently pulled, not searching - {query}")
            # Get children
            node_child_edge_qs = node_obj.edges_as_parent.select_related('child').all().order_by('-weight')
            # Get lists, ordered by weight, highest to lowest
            suggestion_list = node_child_edge_qs.values_list('child__name', flat=True)
            weight_list = node_child_edge_qs.values_list('weight', flat=True)
        # Else, no obj / recent obj
        else:
            # Google search
            url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query_operator)}'
            response_json = requests.request("GET", url).json()
            # Clean suggestions
            raw_suggestion_list = response_json[1]
            raw_weight_list = response_json[4]['google:suggestrelevance'] if 'google:suggestrelevance' in response_json[4] else []
            cleaned_suggestions = clean_suggestions(raw_suggestion_list, raw_weight_list)
            # Form lists
            suggestion_list = cleaned_suggestions['suggestions']
            weight_list = cleaned_suggestions['weights']
        # Return data
        data = {
            # Model info
            'node_obj': node_obj,
            'node_created': node_created,
            # Query info
            'query': query,
            'query_operator': query_operator,
            # Search results
            'suggestions': list(suggestion_list),
            'weights': list(weight_list),
        }
        # Debug
        #settings.DEBUG and print(f"\n{response_json}\n\n{data}")
        return data

    # Make database updates
    def database_update(search_results):
        # Parent info
        parent_obj = search_results['node_obj']
        parent_created = search_results['node_created']
        # Update parent date_children_last_pulled
        parent_obj.date_children_last_pulled = dt_now
        parent_obj.save()
        # If there are any search results
        if search_results['suggestions']:
            # Children - bulk create setup
            child_node_obj_weights = []
            child_node_obj_ids = []
            child_node_obj_id_weight_dict = {}
            for i, child_query in enumerate(search_results['suggestions']):
                # Child node object - if already stored, get
                if child_query in node_query_obj_dict:
                    child_node_obj, child_created = node_query_obj_dict[child_query]
                # Child node object - else, hasn't been stored
                else:
                    # Get/create
                    child_node_obj, child_created = Node.objects.get_or_create(name=child_query)
                    nodes_created[0] += 1 if child_created else 0
                    # Store data
                    node_query_obj_dict[child_query] = (child_node_obj, child_created)
                # Get variables
                child_node_obj_id = child_node_obj.id
                child_weight = search_results['weights'][i]
                # Fill data containers
                child_node_obj_weights.append([child_node_obj, child_weight]) # [obj, 500]
                child_node_obj_ids.append(child_node_obj_id) # [1,2,3,4]
                child_node_obj_id_weight_dict[child_node_obj_id] = child_weight # {1: 500}
            # Children - If parent is new, create edges for all children
            if parent_created:
                for child_node_obj, weight in child_node_obj_weights: 
                    bulk_edge_create.append(Edge(
                        parent=parent_obj,
                        child=child_node_obj,
                        weight=weight,
                    ))
            # Children - Else, parent not new - edges may be added, updated, or deleted
            else:
                # Get children in the database
                db_child_qs = parent_obj.edges_as_parent.select_related('child').all()
                db_child_ids = db_child_qs.values_list('child', flat=True)
                # For each of the database children - UPDATE or DELETE
                for db_child_edge_obj in db_child_qs:
                    # Get ids
                    db_edge_id = db_child_edge_obj.id
                    db_child_id = db_child_edge_obj.child.id
                    # If db child IN current children
                    if db_child_id in child_node_obj_ids:
                        # If weights are different
                        weight_should_be = child_node_obj_id_weight_dict[db_child_id]
                        if db_child_edge_obj.weight != weight_should_be:
                            # UPDATE - and append
                            db_child_edge_obj.weight = weight_should_be
                            bulk_edge_update_weight.append(db_child_edge_obj)
                    # DELETE - since db child NOT in current children
                    else:
                        bulk_edge_delete_ids.append(db_edge_id)
                # For each of the current children
                for child_node_obj, weight in child_node_obj_weights: 
                    # If not already in database
                    if child_node_obj.id not in db_child_ids:
                        # CREATE - since not in database
                        bulk_edge_create.append(Edge(
                            parent=parent_obj,
                            child=child_node_obj,
                            weight=weight,
                        ))
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
            weight = search_results['weights'][i]
            graph_edges.append({
                'from': search_results['query'],
                'to': suggestion,
                'value': weight,
            })

    # Add suggestions to history (already sorted by weight)
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

    # Bulk update
    if bulk_edge_update_weight:
        Edge.objects.bulk_update(bulk_edge_update_weight, ['weight'], batch_size=n_bulk)

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
        # Suggestion history
        print("-" * 100)
        print(f"* {len(suggestion_history) - 1} levels of search")
        for level, suggestions in suggestion_history.items():
            if level != 'all':
                print(f"> {level} - {suggestions}")
        # Database
        print("-" * 100)
        print(f"* Nodes - {nodes_created[0]} created")
        print(f"* Edges - {len(bulk_edge_create)} created, {len(bulk_edge_update_weight)} updated, {len(bulk_edge_delete_ids)} deleted")
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
        print(f"* communicability_exp: {[x[0] for x in communicability_exp if x[0] != clean_query][:10]}")
        print(f"* communicability: {[x[0] for x in communicability if x[0] != clean_query][:10]}")
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