import networkx as nx
import random

#####################################################################################
# Creates vis.js graph data from an edgelist

class Visjs():
    "Class that creates vis.js graph data from an edgelist"

    #################################################
    # Variables

    # Init
    def __init__(self, edgelist, start_node=None, keep_parallel_edges=True):
        
        # Inputs
        self.edgelist = edgelist
        self.start_node = start_node # node to start graph at
        self.keep_parallel_edges = keep_parallel_edges # keep parallel edges or collapse / average them together?

        # Flags
        self.data_hasnt_been_calculated = True

        # Colors
        self.graph_colors = [
            '#fdae6b',
            '#f3e24d',
            '#36c576',
            '#2acdc0'
        ]

        # Edgelist data containers
        self.edgelist_dict = {} # different way of looking at edgelist {'from_node': ['to_node']}

        # Graph data containers
        self.nodes_with_levels_calculated = set() # track to avoid unecessary calculation
        self.graph_node_dict = {} # {'malbec': {'value': 9, 'color': 'hex', 'level': 1}
        self.graph_node_list = [] # Used for node ids ['a','b','c']
        self.graph_data = {
            'nodes': [], # [{'id': 1, 'label': 'x', 'value': 500, 'color': 'hex'}]
            'edges': [], # [{ 'from': 0, 'to': 1, 'value': 1250 }]
        }

    #################################################
    # Internal functions

    # Recursively calc levels of starting node's descendants
    def calculate_descendant_levels(self, starting_node):
        # Variables
        working_nodes_current_level = set({starting_node})
        working_nodes_next_level = set()
        working_level = 0
        # Start loop if starting node has never been calculated
        if starting_node not in self.nodes_with_levels_calculated:
            while True: 
                # If no more nodes to work, end loop
                if not working_nodes_current_level:
                    break
                else:
                    # For each node to work
                    for working_node in working_nodes_current_level:
                        # Add levels if they don't exist 
                        if working_node in self.graph_node_dict:
                            if 'level' not in self.graph_node_dict[working_node]:
                                self.graph_node_dict[working_node]['level'] = working_level
                        else:
                            self.graph_node_dict[working_node] = {'level': working_level} 
                        # Add children to next level if they exist AND they've never been calculated
                        if working_node in self.edgelist_dict:
                            children_not_calculated = set(self.edgelist_dict[working_node]) - set(self.nodes_with_levels_calculated)
                            working_nodes_next_level.update(children_not_calculated)
                    # Log all current level as calculated
                    self.nodes_with_levels_calculated.update(working_nodes_current_level)
                    # Iterate to next level
                    working_nodes_current_level = working_nodes_next_level
                    working_nodes_next_level = set()
                    working_level += 1

    # Calculate graph data
    def calculate_graph_data(self):

        # Calculate graph data only if needed
        if self.data_hasnt_been_calculated:

            # Unflag
            self.data_hasnt_been_calculated = False

            # Start node - Calculate start node if needed
            if not self.start_node:
                # Pick a random node
                self.start_node = random.choice(self.edgelist)[0]

            # Edgelist - Transform into parent/child dict
            for from_node, to_node, value in self.edgelist:
                if from_node in self.edgelist_dict:
                    self.edgelist_dict[from_node].append(to_node)
                else:
                    self.edgelist_dict[from_node] = [to_node]

            # Node levels - calculate node levels for the initial subgraph (the one with the starting node)
            # Any remaining levels will be calculated during the next step
            self.calculate_descendant_levels(self.start_node) 

            # Graph nodes - Create node dict
            for from_node, to_nodes in self.edgelist_dict.items():
                # Make sure levels of parent and all children are calculated
                self.calculate_descendant_levels(from_node)
                # Get node color. Use modulo to always pick a color
                node_color = self.graph_colors[self.graph_node_dict[from_node]['level'] % len(self.graph_colors)]
                # Parent - If node already added
                if from_node in self.graph_node_dict:
                    if 'value' not in self.graph_node_dict[from_node]:
                        self.graph_node_dict[from_node]['value'] = 1
                    if 'color' not in self.graph_node_dict[from_node]:
                        self.graph_node_dict[from_node]['color'] = node_color
                # Parent - If node hasn't been added
                else:
                    self.graph_node_dict[from_node] = {
                        'value': 1,
                        'color': node_color,
                    }
                # Children
                for i, to_node in enumerate(to_nodes):
                    # Get node color. Use modulo to always pick a color
                    node_color = self.graph_colors[self.graph_node_dict[to_node]['level'] % len(self.graph_colors)]
                    # Child - If node already added
                    if to_node in self.graph_node_dict:
                        # Value - update or add
                        if 'value' in self.graph_node_dict[to_node]:
                            self.graph_node_dict[to_node]['value'] += 1 # Size is based on how mny edges go TO that node
                        else:
                            self.graph_node_dict[to_node]['value'] = 1
                        # Color - add
                        if 'color' not in self.graph_node_dict[to_node]:
                            self.graph_node_dict[to_node]['color'] = node_color
                    # Child - If node hasn't been added
                    else:
                        self.graph_node_dict[to_node] = {
                            'value': 1,
                            'color': node_color,
                        }

            # Graph nodes - Make node list from node dict.
            self.graph_node_list = list(self.graph_node_dict.keys())

            # Graph nodes - Convert node dict to list
            for i, node in enumerate(self.graph_node_list):
                self.graph_data['nodes'].append({
                    'id': i,
                    'label': node,
                    'value': self.graph_node_dict[node]['value'], # size of node on graph
                    'color': self.graph_node_dict[node]['color'], # color of node/edges on graph
                })

            # Graph edges - If we're keeping parallel edges, then simply add all
            if self.keep_parallel_edges:
                # Cycle through edge data
                for from_node, to_node, value in self.edgelist:
                    # Get indices
                    from_index = self.graph_node_list.index(from_node)
                    to_index = self.graph_node_list.index(to_node)
                    # Add to graph
                    self.graph_data['edges'].append({
                        'from': from_index,
                        'to': to_index,
                        'value': value, # size of the line
                    })

            # Graph edges - Else, we're collapsing / averaging parallel edges. 
            # Only one edge will be added for each parallel. Need to track all those created and average weights.
            else:
                # Data container
                edge_lookup = {} # {from_index: {to_index: [value]}
                # Cycle through edge data
                for from_node, to_node, value in self.edgelist:
                    # Get indices
                    from_index = self.graph_node_list.index(from_node)
                    to_index = self.graph_node_list.index(to_node)
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
                        self.graph_data['edges'].append({
                            'from': from_index,
                            'to': to_index,
                            'value': sum(values) / len(values),
                        })

    #################################################
    # External functions

    # Output edgelist from graph data. [(from, to, value)]
    # May differ from initial if parallel edges aren't kept.
    def output_edgelist(self):
        # Calculate graph data if needed
        self.calculate_graph_data()
        # Return
        return [(self.graph_node_list[e['from']], self.graph_node_list[e['to']], e['value']) for e in self.graph_data['edges']]

    # Output graph data
    def output_graph_data(self):
        # Calculate graph data if needed
        self.calculate_graph_data()
        # Return
        return self.graph_data

    # Output network stats dict {'Nodes': 123}
    def output_network_stats(self):
        # Make networkx object
        G = nx.MultiDiGraph(self.output_edgelist())
        # Return
        return {
            'Nodes': G.number_of_nodes(),
            'Edges': G.number_of_edges(),
        }