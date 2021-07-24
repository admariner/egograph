
from django.conf import settings
from django.db import connection
from ..models import Node, Edge

import requests # for getting URL
import urllib # parsing url
import json # for parsing json
from time import sleep # rate limiting
import networkx as nx # network analysis
from datetime import datetime, timezone, timedelta # for getting time

#####################################################################################
# Search class

class Search:
    "Class that handles google searching and database updating"

    # Settings
    operator = 'vs' # adds this to each search query if it's not already there
    rate_limit = .05 # time between each query (seconds)
    n_bulk = 100 # bulk update size (100 max)

    # Bulk containers
    bulk_edge_create = []
    bulk_edge_update_weight = []
    bulk_edge_delete_ids = []

    #################################################

    # Print
    def __str__(self):
        return f"<{self.query}>"

    # Init
    def __init__(self, query, debug):

        # Inputs
        self.query = query
        self.debug = debug

        # Variables
        clean_query = query.lower().strip()
        dt_now = datetime.now(timezone.utc)
        dt_30_days_ago = dt_now - timedelta(days=30)

    #################################################
