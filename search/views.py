from django.shortcuts import render
from django.conf import settings
from django.db import connection
from .models import Node, Edge

import requests # for getting URL
import urllib # parsing url
import json # for parsing json
from time import sleep # rate limiting

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

    # Placeholders
    bulk_edge_create = []
    bulk_edge_delete_ids = []

    # Data containers
    clean_query = query.lower().strip()
    nodes = {clean_query: {'value': 1, 'color': '#6baed6'}} # {'a': 2} size of node
    edges = [] # [{ 'from': 0, 'to': 1, 'value': 1250 }]

    #################################################
    # Functions

    # Google search
    def google_search(query):
        url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query)}'
        return requests.request("GET", url).json()

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
    def get_google_data(query):
        # Rate limit
        sleep(rate_limit)
        # Clean - lowercase and no whitespace
        query = query.lower().strip()
        # Clean - remove the operator if it's already there
        query = query if query[-len(operator):] != operator else query[:len(query) - len(operator)].strip()
        # Add operator back
        query_operator = f"{query} {operator}"
        # Google search
        response_json = google_search(query_operator)
        #settings.DEBUG and print(f"\n{response_json}")
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
        #settings.DEBUG and print(f"\n{data}")
        return data

    # Make database updates
    def database_update(search_results):

        # Parent - get or create
        parent_obj, parent_created = Node.objects.get_or_create(name=search_results['query'])

        # Children - bulk create setup
        child_obj_relevance = []
        child_obj_ids = []
        for i, child in enumerate(search_results['suggestions']):
            child_obj, child_created = Node.objects.get_or_create(name=child)
            child_obj_relevance.append([child_obj, search_results['relevance'][i]]) # [obj, 500]
            child_obj_ids.append(child_obj.id)
            
        # If parent is new, match to all children
        if parent_created:
            for child_obj, relevance in child_obj_relevance: 
                bulk_edge_create.append(Edge(
                    parent=parent_obj,
                    child=child_obj,
                    weight=relevance,
                ))

        # Else, parent not new - need to check if any children need to be added or deleted
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

    #################################################
    # 1st level search
    
    # Search and update database
    search1 = get_google_data(query)
    database_update(search1)

    # Update graph data
    for i, suggestion in enumerate(search1['suggestions']):
        # Add node
        if suggestion not in nodes:
            nodes[suggestion] = {
                'value': 1,
                'color': '#87d0af',
            }
        else:
            nodes[suggestion]['value'] += 1
        # Add edge
        weight = search1['relevance'][i]
        edges.append({
            'from': search1['query'],
            'to': suggestion,
            'value': weight,
        })

    #################################################
    # 2nd level search

    # For each child of parent
    for child_query in search1['suggestions']:

        # Search and update database
        search2 = get_google_data(child_query)
        database_update(search2)

        # Update graph data
        for i, suggestion in enumerate(search2['suggestions']):
            # Add node
            if suggestion not in nodes:
                nodes[suggestion] = {
                    'value': 1,
                    'color': '#fdae6b',
                }
            else:
                nodes[suggestion]['value'] += 1
            # Add edge
            weight = search2['relevance'][i]
            edges.append({
                'from': search2['query'],
                'to': suggestion,
                'value': weight,
            })

    #################################################
    # Edge - bulk actions

    # Bulk create
    if bulk_edge_create:
        settings.DEBUG and print(f"* Edge - bulk create {len(bulk_edge_create)}.")
        Edge.objects.bulk_create(bulk_edge_create, batch_size=n_bulk, ignore_conflicts=True) # ignore errors

    # Bulk delete
    if bulk_edge_delete_ids:
        settings.DEBUG and print(f"* Edge - bulk delete {len(bulk_edge_delete_ids)}.")
        # Chunk deletions
        i_start = 0
        i_end = n_bulk
        while i_start < len(bulk_edge_delete_ids):
            Edge.objects.filter(id__in=bulk_edge_delete_ids[i_start:i_end]).delete()
            i_start = i_end
            i_end += n_bulk

    # Debug
    if settings.DEBUG and connection.queries:
        #for q in connection.queries:
        #    print(q)
        print(f"* Made {len(connection.queries)} queries to the database")

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
    node_list = list(nodes.keys())
    for i, node in enumerate(node_list):
        graph_data['nodes'].append({
            'id': i,
            'value': nodes[node]['value'],
            'label': node,
            'color': nodes[node]['color'],
        })

    # Add edges
    for edge in edges:
        # Get indices
        from_index = node_list.index(edge['from'])
        to_index = node_list.index(edge['to'])

        # Check if combo already exists (only show one line)
        if from_index in edge_combos:
            if to_index in edge_combos[from_index]:
                continue # skip loop
            else:
                edge_combos[from_index].append(to_index)
        else:
            edge_combos[from_index] = [to_index]

        # Check if combo already exists (only show one line)
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

    # Render
    return render(request, 'search/result.html', context = {
        'input_value': clean_query,
        'graph_data': json.dumps(graph_data),
    })