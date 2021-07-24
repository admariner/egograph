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

    # History
    search_history = {} # {1: {'query': {'level': 1, 'suggestions': ['a', 'b'], 'weights': [600, 400]}} # sorted by weight
    suggestion_history = {} # {1: ['a'], 2: ['b', 'c']} # sorted by weight

    # Data containers
    nodes_created = [0]
    node_query_obj_dict = {} # {'blueberry': (node_obj, node_created)}

    # Graph
    collapse_parallel_edges_on_graph = True # average parallel edges together into one value
    graph_colors = [
        '#fdae6b',
        '#f3e24d',
        '#36c576',
        '#2acdc0'
    ]

    #c5493c
    #6baed6
    #87d0af
    #0ca798

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

    # Clean google data to remove query (the query can sometimes change)
    def clean_google_data(suggestion_list, weight_list):
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

    # Get search data
    def get_search_data(query, level):
        # Rate limit
        sleep(rate_limit)
        # Clean - lowercase and no whitespace
        query = query.lower().strip()
        # Clean - remove the operator if it's already there
        query = query if query[-len(operator):] != operator else query[:len(query) - len(operator)].strip()
        # Add operator back
        query_and_operator = f"{query} {operator}"
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
            # Get children
            node_child_edge_qs = node_obj.edges_as_parent.select_related('child').all().order_by('-weight')
            # Get lists, ordered by weight, highest to lowest
            suggestion_list = node_child_edge_qs.values_list('child__name', flat=True)
            weight_list = node_child_edge_qs.values_list('weight', flat=True)
        # Else, no obj / recent obj
        else:
            # Google search
            url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query_and_operator)}'
            response_json = requests.request("GET", url).json()
            # Clean suggestions
            raw_suggestion_list = response_json[1]
            raw_weight_list = response_json[4]['google:suggestrelevance'] if 'google:suggestrelevance' in response_json[4] else []
            google_data = clean_google_data(raw_suggestion_list, raw_weight_list)
            # Form lists
            suggestion_list = google_data['suggestions']
            weight_list = google_data['weights']
        # Create data to return
        data = {
            # Model info
            'node_obj': node_obj,
            'node_created': node_created,
            # Query info
            'query': query,
            'query_and_operator': query_and_operator,
            # Search results
            'suggestions': list(suggestion_list),
            'weights': list(weight_list),
        }
        # History - searches (sorted by weight). Use copy to avoid bugs.
        search_history[query] = {
            'level': level,
            'suggestions': data['suggestions'].copy(),
            'weights': data['weights'].copy(),
        }
        # History - suggestions history (sorted by weight)
        if level in suggestion_history and isinstance(suggestion_history[level], list): 
            suggestion_history[level].extend(data['suggestions'])
        else:
            suggestion_history[level] = data['suggestions']
        # Return
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

    # Perform bulk database actions
    def database_bulk_actions():
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

    # Create edgelist [(from, to, value)]
    def create_edgelist():
        # Placeholder
        data = []
        # For each query 
        for from_node, to_results in search_history.items():
            # For each suggestion
            for i, to_node in enumerate(to_results['suggestions']):
                # Add to edgelist
                value = to_results['weights'][i]
                data.append((from_node, to_node, value))
        # Return
        return data

    # Create graph data
    def create_graph_data():
        pass

    #################################################
    # Google search, update database, update graph data

    # 1st level search
    search1 = get_search_data(clean_query, 1)
    database_update(search1)

    # For each child of 1st level (if it exists)
    if 1 in suggestion_history:
        for child1_query in suggestion_history[1]:

            # 2nd level search
            search2 = get_search_data(child1_query, 2)
            database_update(search2)

    # Make list of unique nodes
    unique_nodes = set()
    for level, suggestions in suggestion_history.items():
        for s in suggestions:
            unique_nodes.add(s)

    # If there's not enough nodes
    if len(unique_nodes) <= 15:

        # For each child of 2nd level (if it exists)
        if 2 in suggestion_history:
            for child2_query in suggestion_history[2]:

                # 3rd level search
                search3 = get_search_data(child2_query, 3)
                database_update(search3)

    # Perform db bulk create, update, delete
    database_bulk_actions()

    ########################################################
    # Graph - settings and placeholders

    # Data containers
    graph_node_dict = {clean_query: {'value': 1, 'color': graph_colors[0]}} # {'malbec': {'value': 9, 'color': 'hex'}
    graph_data = {
        'nodes': [], # [{'id': 1, 'label': 'x', 'value': 500, 'color': 'hex'}]
        'edges': [], # [{ 'from': 0, 'to': 1, 'value': 1250 }]
    }

    ########################################################
    # Create graph data

    # Create node dict
    for search_query, search_results in search_history.items():
        # For each suggestion
        for i, suggestion in enumerate(search_results['suggestions']):
            # If already added, update
            if suggestion in graph_node_dict:
                graph_node_dict[suggestion]['value'] += 1 # increases size of node
            # Else, add
            else:
                graph_node_dict[suggestion] = {
                    'value': 1,
                    'color': graph_colors[search_results['level']],
                }

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

    # Edges - if we're allowing parallel edges, then simply add all
    if not collapse_parallel_edges_on_graph:
        # Cycle through edge data
        for from_node, to_node, value in create_edgelist():
            # Get indices
            from_index = graph_node_list.index(from_node)
            to_index = graph_node_list.index(to_node)
            # Add to graph
            graph_data['edges'].append({
                'from': from_index,
                'to': to_index,
                'value': value,
            })

    # Edges - else, we're collapsing parallel edges. 
    # Only one edge will be added for each parallel. Need to track all those created and average weights.
    else:
        # Data container
        edge_lookup = {} # {from_index: {to_index: [value]}
        # Cycle through edge data
        for from_node, to_node, value in create_edgelist():
            # Get indices
            from_index = graph_node_list.index(from_node)
            to_index = graph_node_list.index(to_node)
            # 1) Need to check if a from/to or to/from exists
            existing_edge_type = None # 'from_to' or 'to_from'
            if from_index in edge_lookup and to_index in edge_lookup[from_index]: # from/to
                existing_edge_type = 'from_to'
            elif to_index in edge_lookup and from_index in edge_lookup[to_index]: # to/from
                existing_edge_type = 'to_from'
            # 2) If nothing already exists, log new data
            if not existing_edge_type:
                if from_index in edge_lookup:
                    edge_lookup[from_index][to_index] = [value]
                else:
                    edge_lookup[from_index] = {to_index: [value]}
            # 3) Else, something exists, add value to that edge
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
    # Networkx

    # Create edge list - always use graph data so they match
    graph_edgelist = [(graph_node_list[e['from']], graph_node_list[e['to']], e['value']) for e in graph_data['edges']] # [(from, to, value)]

    # Make graph 
    G = nx.MultiDiGraph(graph_edgelist)
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

    # Centrality - degree
    centrality_degree = [(n, v) for n,v in nx.degree_centrality(G).items()]
    centrality_degree.sort(key=lambda x:x[1])
    centrality_degree.reverse()

    ########################################################
    # Rank google suggestions

    # Create list of all suggestions
    all_suggestions = []

    # Get a sorted list of the search history keys
    suggestion_history_keys = list(suggestion_history.keys())
    suggestion_history_keys.sort()

    # For each search level, add to the list
    for level in suggestion_history_keys:
        for s in suggestion_history[level]:
            all_suggestions.append(s)
 
    # Create ranked list of google suggestions
    google_suggestions_ranked = [] 
    [google_suggestions_ranked.append(s) for s in all_suggestions if s not in google_suggestions_ranked and s != clean_query]

    ########################################################
    # Debug

    if settings.DEBUG:
        # Suggestion history
        print("-" * 100)
        print(f"* {len(suggestion_history)} levels of search")
        for level, suggestions in suggestion_history.items():
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
        n_rankings = 5
        n_ljust = 25
        #
        print(f"* {'Google autocomplete'.ljust(n_ljust)} - {google_suggestions_ranked[:n_rankings]}")
        print(f"* {'Communicability (exp)'.ljust(n_ljust)} - {[x[0] for x in communicability_exp if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Communicability'.ljust(n_ljust)} - {[x[0] for x in communicability if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Deg. centrality'.ljust(n_ljust)} - {[x[0] for x in centrality_degree if x[0] != clean_query][:n_rankings]}")
        print(f"* {'Voterank (undir)'.ljust(n_ljust)} - {[x for x in nx.voterank(G2) if x != clean_query][:n_rankings]}")
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
        # Fin
        print("-" * 100)

    ########################################################
    # Render

    # Number of suggestions to show
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