from django.http import HttpResponse # http response

from search.models import Edge

from datetime import datetime, timezone # for getting time
import csv # for making csv files
import zipfile # for making zip files
from io import BytesIO, StringIO # store data in memory

#####################################################################################
# Export edgelist

def edgelist(request):

    # Name of file
    filename = "EgoGraph edgelist"

    # Get today's date for file names
    date_today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Create edge list
    edgelist = list(Edge.objects.values_list('parent__name', 'child__name', 'weight'))

    # Make in-memory zip file
    mem_zip = BytesIO()

    # Write files to in-mem zip
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        # Make in-memory csv
        mem_csv = StringIO()
        writer = csv.writer(mem_csv, delimiter=' ')

        # Clean text function. Turns "e k" into "e_k"
        def clean_name(name):
            temp = name.split()
            return "_".join(temp)

        for parent, child, value in edgelist:
            writer.writerow([clean_name(parent), clean_name(child), value])

        # Add to zip file
        zf.writestr(f"{date_today} {filename}.txt", mem_csv.getvalue())

    #########################################
    # Return the in-memory zip file as a download
        
    response = HttpResponse(mem_zip.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f"attachment; filename={date_today} {filename}.zip"

    return response