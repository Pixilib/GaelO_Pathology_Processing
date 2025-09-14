from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, HttpResponse
from ...exceptions import GaelONotFoundException

from gaelo_pathology_processing.services.file_helper import get_file, is_file_exists, delete_file


class DicomView(APIView):
    def get(self, request: Request, id: str) -> HttpResponse:
        """Retrieves a ZIP containing the DICOM folder associated with the given ID and downloads it from storage."""
        try:
            file = get_file('dicoms', id + '.zip')
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{
                id}.zip"'
            response['Content-Type'] = 'application/zip'

            return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    def delete(self, request : Request, id : str):
        if not is_file_exists('dicoms', id):
            raise GaelONotFoundException("File doesn't exist")
        delete_file('dicoms', id)
        return Response(status=200)
