from flask import Flask # main app
from flask import render_template # route to a template
from flask import abort # abort to an error page
#
import requests # for getting URL
import urllib # parsing url
import json # for parsing json
from time import sleep

#################################################################
# Initialize

app = Flask(__name__)
app.debug = False

#################################################################
# URL ROUTES

# landing
@app.route('/')
def landing():
    return render_template('landing.html')

# Error - 404
@app.errorhandler(404)
def page_not_found_error(e):
    alert = 'Error 404 - Page not found. If you see this, please contact twitter.com/EdwardKerstein'
    return render_template('landing.html', alert=alert), 404

# Error - 500
@app.errorhandler(500)
def internal_server_error(e):
    alert = 'Error 500 - Internal server error. If you see this, please contact twitter.com/EdwardKerstein'
    return render_template('landing.html', alert=alert), 500

################################################################################################################

# Google search
def google_search(query):
    url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query)}'
    return requests.request("GET", url).json()

# Exclude func
def not_excluded(suggestion_word_split):
    # Exclude words
    exclude_words = ['or', 'vs', 'and']
    # Not blank
    if suggestion_word_split:
        # Not excluded words
        if not any(x in suggestion_word_split for x in exclude_words):
            # Not 1 character
            if not (len(suggestion_word_split) == 1 and len(suggestion_word_split[0]) == 1):
                return True

# Clean suggestions func
def clean_suggestions(suggestion_list, data_array, operator):
    # For each suggestion
    for s in suggestion_list:
        # Split words
        s_split = s.split()
        # For each word
        for word in s.split():
            s_split.remove(word)
            if word == operator.strip():
                break
        # Check exclusions
        if not_excluded(s_split):
            # Turn into string
            data_array.append(' '.join(s_split))

# Charts & Dashboards
@app.route("/graph/<path:query>")
def result(query):
    try:
        # Clean
        clean_query1 = query.lower().strip()

        # Add versus if needed
        operator = ' vs '  
        query1 = clean_query1
        query1 += operator if query1[-len(operator):] != operator else ''

        # Data containers
        nodes = {clean_query1: {'value': 1, 'color': '#6baed6'}} # {'a': 2} size of node
        edges = [] # [{ 'from': 0, 'to': 1, 'value': 1250 }]

        ########################################################

        # First level search
        response_json1 = google_search(query1)

        # Clean suggestions
        clean_suggestions1 = []
        clean_suggestions(response_json1[1], clean_suggestions1, operator)

        # Add edges
        for index, suggest1 in enumerate(clean_suggestions1):
            # Add node
            if suggest1 not in nodes:
                nodes[suggest1] = {
                    'value': 1,
                    'color': '#87d0af',
                }
            else:
                nodes[suggest1]['value'] += 1
            # Add edge
            weight = response_json1[4]['google:suggestrelevance'][index]
            edges.append({
                'from': clean_query1,
                'to': suggest1,
                'value': weight,
            })

        ########################################################

        # Second level search
        for query2 in clean_suggestions1:

            # Rate limit
            sleep(.05)

            # Add operator if needed
            clean_query2 = query2
            query2 += operator if query2[-len(operator):] != operator else ''

            # Google search
            response_json2 = google_search(query2)

            # Clean suggestions
            clean_suggestions2 = []
            clean_suggestions(response_json2[1], clean_suggestions2, operator)

            # 2nd level suggestions
            for index, suggest2 in enumerate(clean_suggestions2):
                # Add node
                if suggest2 not in nodes:
                    nodes[suggest2] = {
                        'value': 1,
                        'color': '#fdae6b',
                    }
                else:
                    nodes[suggest2]['value'] += 1
                # Add edge
                weight = response_json2[4]['google:suggestrelevance'][index]
                edges.append({
                    'from': clean_query2,
                    'to': suggest2,
                    'value': weight,
                })

        ########################################################

        # Form graph data
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
        return render_template('result.html', input_value=clean_query1, graph_data=json.dumps(graph_data))

    # If exception raised
    except:
        try:
            return render_template('landing.html', alert=alert, input_value=clean_query1), 404
        except:
            abort(500)

#################################################################
# RUN FLASK

if __name__ == "__main__":
    app.run()