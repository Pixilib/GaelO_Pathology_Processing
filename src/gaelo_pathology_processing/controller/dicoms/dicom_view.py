from rest_framework.request import Request
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from rest_framework.views import APIView
from gaelo_pathology_processing.services.file_helper import get_file

class DicomView(APIView):    
    def get(self, request: Request, id: str) -> HttpResponse:
        """Retrieves a ZIP containing the DICOM folder associated with the given ID and downloads it from storage."""
        try:
            # Accéder au storage 'dicoms'
            file = get_file('dicoms',id + '.zip' )     

            # Crée la réponse pour le téléchargement
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{id}.zip"'
            response['Content-Type'] = 'application/zip'

            return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)
            
