from django.core.management.base import BaseCommand, CommandError

from search.models import Node, Edge

#####################################################################################

class Command(BaseCommand):
    help = 'Delete nodes that no longer have any edges'

    # Optional arguments
    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete nodes without edges')

    # Command
    def handle(self, *args, **options):
        # Try to run command
        try:
            # Create node/edge sets
            node_set = set(Node.objects.values_list('id', flat=True))
            edge_set = set(Edge.objects.values_list('parent_id', flat=True)).union(set(Edge.objects.values_list('child_id', flat=True)))
            # Create list of nodes without edges
            nodes_without_edges = list(node_set - edge_set)
            # Delete
            if options['delete']:
                # Settings
                n_bulk = 100 # bulk delete
                # Chunk deletions
                i_start = 0
                i_end = n_bulk
                while i_start < len(nodes_without_edges):
                    Node.objects.filter(id__in=nodes_without_edges[i_start:i_end]).delete()
                    i_start = i_end
                    i_end += n_bulk
        except:
            raise CommandError("FAIL: couldn't pull node data.")
        # Return
        self.stdout.write(self.style.SUCCESS(f"{len(nodes_without_edges)} nodes without edges{' - DELETED' if options['delete'] else ''}"))