from django.http import HttpResponse # http response

from core.classes.network import Network

from datetime import datetime, timezone # for getting time
import zipfile # for making zip files
from io import BytesIO, StringIO # store data in memory

#####################################################################################
# Export edgelist

def edgelist(request):

    # Name of file
    filename = "EgoGraph edgelist"

    # Get today's date for file names
    date_today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Make in-memory zip file
    mem_zip = BytesIO()

    # Write files to in-mem zip
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        # Make in-memory csv
        mem_csv = StringIO()

        # Write edgelist to file
        network = Network()
        network.write_edgelist_to_file(mem_csv)

        # Add to zip file
        zf.writestr(f"{date_today} {filename}.edges", mem_csv.getvalue())

    #########################################
    # Return the in-memory zip file as a download
        
    response = HttpResponse(mem_zip.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f"attachment; filename={date_today} {filename}.zip"

    return response