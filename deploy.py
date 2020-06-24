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

# Charts & Dashboards
@app.route("/graph/<path:query>")
def result(query):
    try:
        # Operator
        operator = ' vs'

        # Form query      
        query1 = query.lower()
        query1 += operator if query1[-len(operator):] != operator else ''

        # Clean
        clean_query1 = query1[:-len(operator)]

        # Request
        url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query1)}'
        response_json = requests.request("GET", url).json()

        # Containers
        nodes = {clean_query1: {'value': 1, 'color': '#6baed6'}} # {'a': 2} size of node
        edges = [] # [{ 'from': 0, 'to': 1, 'value': 1250 }]

        # Exclude words
        exclude_words = ['or', 'vs', 'and']

        # Clean suggestions
        clean_suggestions1 = []
        for s in response_json[1]:
            clean_s = s[len(query1):].strip()
            clean_s_split = clean_s.split()
            if not any(x in clean_s_split for x in exclude_words):
                clean_suggestions1.append(clean_s)

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
            weight = response_json[4]['google:suggestrelevance'][index]
            edges.append({
                'from': clean_query1,
                'to': suggest1,
                'value': weight,
            })

        # Second level search
        for query2 in clean_suggestions1:

            # Rate limit
            sleep(.05)

            # Lookup
            clean_query2 = query2
            query2 += operator if query2[-len(operator):] != operator else ''
            url = f'http://suggestqueries.google.com/complete/search?&output=chrome&gl=us&hl=en&q={urllib.parse.quote(query2)}'
            response_json2 = requests.request("GET", url).json()

            # Clean suggestions
            clean_suggestions2 = []
            for s in response_json2[1]:
                clean_s = s[len(query2):].strip()
                clean_s_split = clean_s.split()
                if not any(x in clean_s_split for x in exclude_words):
                    clean_suggestions2.append(clean_s)

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

        # Render
        return render_template('result.html',input_value=query, graph_data=json.dumps(graph_data))

    # If exception raised
    except:
        try:
            # 404 to landing page with alert
            return render_template('landing.html', alert=alert, input_value=query), 404
        except:
            # If exception not captured, abort to 500
            abort(500)

#################################################################
# RUN FLASK

if __name__ == "__main__":
    app.run()