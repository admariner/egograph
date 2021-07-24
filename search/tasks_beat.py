from celery import shared_task

from .models import Node
from .classes.search import Search

from datetime import datetime, timezone, timedelta # for datetimes

#####################################################################################
# Pull children for nodes that haven't done so yet

@shared_task
def pull_children_for_nodes_without_them():

    # Pull the earliest created node that hasn't had its children pulled
    node_obj = Node.objects.filter(date_children_last_pulled__isnull=True).earliest('date_created')

    # If obj
    if node_obj:

        # Debug
        print(f"Celery beat - {node_obj.name} children pulled.")


    '''
    # Get google search data
    search_results = google_search(node_obj.name)

    # Update database
    # Calc 48 hour ago datetime
    two_days_ago_datetime = datetime.now(timezone.utc) - timedelta(days=2)

    # Get all files created more than 2 days ago
    expired_files = FileExport.objects.filter(date_created__lte=two_days_ago_datetime).exclude(file_export="")

    # If any exist
    if expired_files.exists():

        # Debug
        print(f"Celery beat - {expired_files.count()} expired files deleted.")

        # Delete file only, keep record
        # Use delete() to sync to S3
        for f in expired_files:
            f.file_export.delete()

    '''

    # Return
    return
