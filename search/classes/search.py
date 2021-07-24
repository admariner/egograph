
from django.conf import settings
from django.db import connection
from ..models import Node, Edge

import requests # for getting URL
import urllib # parsing url
from time import sleep # rate limiting
from datetime import datetime, timezone, timedelta # for getting time

#####################################################################################
# Search class

class Search:
    "Class that handles google searching and database updating"

    #################################################
    # Variables

    # Init
    def __init__(self):
        
        # Settings
        self.operator = 'vs' # adds this to each search query if it's not already there
        self.rate_limit = .05 # time between each query (seconds)
        self.n_bulk = 100 # bulk update size (100 max)

        # Dates
        self.dt_now = datetime.now(timezone.utc)
        self.dt_30_days_ago = self.dt_now - timedelta(days=30)

        # Node information
        self.nodes_created = 0
        self.node_query_obj_dict = {} # {'blueberry': (node_obj, node_created)}

        # Search history
        self.search_history = {} # {1: {'query': {'level': 1, 'suggestions': ['a', 'b'], 'weights': [600, 400]}} # sorted by weight
        self.suggestion_history = {} # {1: ['a'], 2: ['b', 'c']} # sorted by weight

        # Bulk containers
        self.bulk_edge_create = []
        self.bulk_edge_update_weight = []
        self.bulk_edge_delete_ids = []

    #################################################
    # Functions

    # Check words to see if they're allowed
    def not_excluded(self, suggestion_word_split):
        # Exclude words
        exclude_words = [self.operator] # used to be 'vs', 'or', 'and'
        # If not blank
        if suggestion_word_split:
            # Not excluded words
            if not any(x in suggestion_word_split for x in exclude_words):
                # Not 1 character
                if not (len(suggestion_word_split) == 1 and len(suggestion_word_split[0]) == 1):
                    return True

    # Clean google data to remove query (the query can sometimes change)
    def clean_google_data(self, suggestion_list, weight_list):
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
                if word == self.operator.strip():
                    break
            # If the word isn't excluded
            if self.not_excluded(word_split):
                # Join words back into phrase and add to results
                results['suggestions'].append(' '.join(word_split))
                results['weights'].append(weight)
        # Return
        return results

    # Get search data
    def google_and_prep_database(self, query, level):
        # Clean - lowercase and no whitespace
        query = query.lower().strip()
        # Clean - remove the operator if it's already there
        query = query if query[-len(self.operator):] != self.operator else query[:len(query) - len(self.operator)].strip()
        # Add operator back
        query_and_operator = f"{query} {self.operator}"
        # Node object - if already stored, get
        if query in self.node_query_obj_dict:
            node_obj, node_created = self.node_query_obj_dict[query]
        # Node object - else, hasn't been stored
        else:
            # Get/create
            node_obj, node_created = Node.objects.get_or_create(name=query)
            self.nodes_created += 1 if node_created else 0
            # Store data
            self.node_query_obj_dict[query] = (node_obj, node_created)
        # Check if this query has recently been pulled in the database
        node_recently_pulled = False
        if node_obj.date_children_last_pulled and self.dt_30_days_ago:
            node_recently_pulled = node_obj.date_children_last_pulled >= self.dt_30_days_ago
        # If node recently pulled
        if node_recently_pulled:
            # Get children
            node_child_edge_qs = node_obj.edges_as_parent.select_related('child').all().order_by('-weight')
            # Get lists, ordered by weight, highest to lowest
            suggestion_list = node_child_edge_qs.values_list('child__name', flat=True)
            weight_list = node_child_edge_qs.values_list('weight', flat=True)
        # Else, no obj / recent obj
        else:
            # Rate limit
            sleep(self.rate_limit)
            # Google search
            url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query_and_operator)}'
            response_json = requests.request("GET", url).json()
            # Clean suggestions
            raw_suggestion_list = response_json[1]
            raw_weight_list = response_json[4]['google:suggestrelevance'] if 'google:suggestrelevance' in response_json[4] else []
            google_data = self.clean_google_data(raw_suggestion_list, raw_weight_list)
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
        # History - search data (sorted by weight). Only add if unique. Use copy to avoid bugs.
        if query not in self.search_history:
            self.search_history[query] = {
                'level': level,
                'suggestions': data['suggestions'].copy(),
                'weights': data['weights'].copy(),
            }
        # History - suggestions history (sorted by weight)
        if level in self.suggestion_history and isinstance(self.suggestion_history[level], list): 
            self.suggestion_history[level].extend(data['suggestions'])
        else:
            self.suggestion_history[level] = data['suggestions']
        # Make database updates
        self.database_update(data)
        # Return
        return data

    # Make database updates
    def database_update(self, search_results):
        # Parent info
        parent_obj = search_results['node_obj']
        parent_created = search_results['node_created']
        # Update parent date_children_last_pulled
        parent_obj.date_children_last_pulled = self.dt_now
        parent_obj.save()
        # If there are any search results
        if search_results['suggestions']:
            # Children - bulk create setup
            child_node_obj_weights = []
            child_node_obj_ids = []
            child_node_obj_id_weight_dict = {}
            for i, child_query in enumerate(search_results['suggestions']):
                # Child node object - if already stored, get
                if child_query in self.node_query_obj_dict:
                    child_node_obj, child_created = self.node_query_obj_dict[child_query]
                # Child node object - else, hasn't been stored
                else:
                    # Get/create
                    child_node_obj, child_created = Node.objects.get_or_create(name=child_query)
                    self.nodes_created += 1 if child_created else 0
                    # Store data
                    self.node_query_obj_dict[child_query] = (child_node_obj, child_created)
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
                    self.bulk_edge_create.append(Edge(
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
                            self.bulk_edge_update_weight.append(db_child_edge_obj)
                    # DELETE - since db child NOT in current children
                    else:
                        self.bulk_edge_delete_ids.append(db_edge_id)
                # For each of the current children
                for child_node_obj, weight in child_node_obj_weights: 
                    # If not already in database
                    if child_node_obj.id not in db_child_ids:
                        # CREATE - since not in database
                        self.bulk_edge_create.append(Edge(
                            parent=parent_obj,
                            child=child_node_obj,
                            weight=weight,
                        ))

    # Perform bulk database actions
    def database_bulk_actions(self, debug=settings.DEBUG):
        # Bulk create
        if self.bulk_edge_create:
            Edge.objects.bulk_create(self.bulk_edge_create, batch_size=self.n_bulk, ignore_conflicts=True) # ignore errors
        # Bulk update
        if self.bulk_edge_update_weight:
            Edge.objects.bulk_update(self.bulk_edge_update_weight, ['weight'], batch_size=self.n_bulk)
        # Bulk delete
        if self.bulk_edge_delete_ids:
            # Chunk deletions
            i_start = 0
            i_end = self.n_bulk
            while i_start < len(self.bulk_edge_delete_ids):
                Edge.objects.filter(id__in=self.bulk_edge_delete_ids[i_start:i_end]).delete()
                i_start = i_end
                i_end += self.n_bulk
        # Debug
        if debug:
            print(f"* Nodes - {self.nodes_created} created")
            print(f"* Edges - {len(self.bulk_edge_create)} created, {len(self.bulk_edge_update_weight)} updated, {len(self.bulk_edge_delete_ids)} deleted")
            print(f"* Database -  {len(connection.queries) if connection.queries else 0} queries") 
