from django.core.management.base import BaseCommand, CommandError

from core.classes.network import Network

#####################################################################################

class Command(BaseCommand):
    help = 'Imports edgelist to database from file.'

    # Required arguments
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='File path of edgelist.')

    # Command
    def handle(self, *args, **options):
        # Try to run command
        try:
            # Make network object
            network = Network()
            # Import
            network.import_edgelist_from_file(options['file_path'])
        except:
            raise CommandError("FAIL: couldn't import edgelist to database.")
        # Return
        self.stdout.write(self.style.SUCCESS(f"Imported edgelist successfully."))