from pathlib import Path
import tempfile
from openslide import (OpenSlide)
from django.http import FileResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from gaelo_pathology_processing.services.file_helper import get_file, move_to_storage, get_hash
from gaelo_pathology_processing.services.utils import find_wsi_file


class WsiView(APIView):
    """
    Upload a wsi image
    """

    def post(self, request: Request):
        try:
            binary_data = request.body
            with tempfile.NamedTemporaryFile(suffix="", delete=False) as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name

            file_hash = get_hash(temp_file_path)
            format = OpenSlide.detect_format(temp_file_path)
            print(format)

            if format is None:
                return Response({'error': 'Invalid file or unsupported format'}, status=400)

            move_to_storage('wsi', str(temp_file_path), file_hash)

            return Response({
                'id': file_hash
            }, status=200)

        except Exception as e:
            return Response({'error': f'{str(e)}'}, status=500)

    def get(self, request: Request, id: str):
        try:
            wsi_file_path = find_wsi_file(id)
            file = get_file('wsi', wsi_file_path)
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{id}"'
            response['Content-Type'] = 'application/octet-stream'

            return response
        except Exception as e:
            return Response({"error": str(e)}, status=500)
