from celery import shared_task

from core.classes.network import Network

#####################################################################################
# Delete nodes without edges

@shared_task
def delete_nodes_without_edges():
    # Make network object
    network = Network()
    # Delete nodes without edges
    nodes_deleted = network.nodes_without_edges(delete=True)
    # Debug
    if nodes_deleted:
        print(f'Celery beat - {nodes_deleted} nodes without edges deleted')
    # Return
    return


