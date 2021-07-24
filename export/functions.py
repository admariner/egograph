from search.models import Node, Edge

#####################################################################################
# Delete nodes without edges

def delete_nodes_without_edges():

    # Create node/edge sets
    node_set = set(Node.objects.values_list('id', flat=True))
    edge_set = set(Edge.objects.values_list('parent_id', flat=True)).union(set(Edge.objects.values_list('child_id', flat=True)))

    # Create list of nodes without edges
    nodes_without_edges = list(node_set - edge_set)

    # Bulk size
    n_bulk = 100

    # Chunk deletions
    i_start = 0
    i_end = n_bulk
    while i_start < len(nodes_without_edges):
        Node.objects.filter(id__in=nodes_without_edges[i_start:i_end]).delete()
        i_start = i_end
        i_end += n_bulk