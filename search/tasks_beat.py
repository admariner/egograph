from celery import shared_task

from search.models import Node
from search.classes import Search

#####################################################################################
# Pull children for nodes that haven't done so yet

@shared_task
def pull_children_for_nodes_without_them():

    # Pull the earliest created node that hasn't had its children pulled
    node_obj = Node.objects.filter(date_children_last_pulled__isnull=True).earliest('date_created')

    # If obj
    if node_obj:

        # Debug
        print(f'Celery beat - "{node_obj.name}" searched')

        # Make search object
        search = Search()

        # Perform search
        search.google_and_prep_database(node_obj.name, 1)

        # Perform db bulk create, update, delete
        search.database_bulk_actions(debug=True)

    # Return
    return
