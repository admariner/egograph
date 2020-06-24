import networkx as nx
import matplotlib.pyplot as plt
import requests
import urllib.parse
from time import sleep
  
#########################################################

query1 = 'poodle'.lower()

# Add string
operator = ' vs'
query1 += operator

# Clean
clean_query1 = query1.replace('vs', '').strip()

# Query
url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query1)}'
response_json = requests.request("GET", url).json()

# Containers
nodes = {clean_query1: 100} # {'a': 2} size of node
edges = [] # [('a', 'b', 5.0)]
colors = ['red']

# Exclude words
exclude_words = ['or', 'vs', 'and']

# Clean suggestions
clean_suggestions1 = []
for s in response_json[1]:
    clean_s = s.replace(query1, '').strip()
    clean_s_split = clean_s.split()
    if not any(x in clean_s_split for x in exclude_words):
        clean_suggestions1.append(clean_s)

# Add edges
for index, suggestion in enumerate(clean_suggestions1):
    # Add node
    if suggestion not in nodes:
        nodes[suggestion] = 100
        colors.append('green')
    else:
        nodes[suggestion] += 200
    # Add edge
    weight = response_json[4]['google:suggestrelevance'][index]
    edges.append((clean_query1, suggestion, {'weight': weight, 'distance': weight}))

# Look up suggestions
for query2 in clean_suggestions1:

    sleep(.1)

    # Lookup
    clean_query2 = query2
    query2 += operator
    url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query2)}'
    response_json2 = requests.request("GET", url).json()

    # Clean suggestions
    clean_suggestions2 = []
    for s in response_json2[1]:
        clean_s = s.replace(query2, '').strip()
        clean_s_split = clean_s.split()
        if not any(x in clean_s_split for x in exclude_words):
            clean_suggestions2.append(clean_s)

    # 2nd level suggestions
    for index, suggest2 in enumerate(clean_suggestions2):
        # Add node
        if suggest2 not in nodes:
            nodes[suggest2] = 100
            colors.append('blue')
        else:
            nodes[suggest2] += 200
        # Add edge
        weight = response_json2[4]['google:suggestrelevance'][index]
        edges.append((clean_query2, suggest2, {'weight': weight, 'distance': weight}))

# Create graph and add data
G = nx.Graph()
G.add_nodes_from(nodes)
G.add_weighted_edges_from([(e[0], e[1], e[2]['weight']) for e in edges])

# Create ego graph of main hub
egograph = nx.ego_graph(G, clean_query1, center=True, distance='distance', radius=100000)

# Draw
nx.draw_networkx(egograph, node_color=colors, node_size=[size for k,size in nodes.items()])
plt.show()
