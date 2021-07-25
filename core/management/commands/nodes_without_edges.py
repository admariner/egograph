from django.core.management.base import BaseCommand, CommandError

from core.classes.network import Network

#####################################################################################

class Command(BaseCommand):
    help = 'Counts nodes that no longer have any edges and can delete them.'

    # Optional arguments
    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Delete nodes without edges')

    # Command
    def handle(self, *args, **options):
        # Try to run command
        try:
            # Make network object
            network = Network()
            # Pull nodes without edges
            nodes_without_edges = network.nodes_without_edges()
            # Delete
            if options['delete']:
                network.nodes_without_edges(delete=True)
        except:
            raise CommandError("FAIL: couldn't pull nodes without edges.")
        # Return
        self.stdout.write(self.style.SUCCESS(f"{nodes_without_edges} nodes without edges{' - DELETED' if options['delete'] else ''}"))