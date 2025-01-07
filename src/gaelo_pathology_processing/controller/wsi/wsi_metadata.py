from gaelo_pathology_processing.services.utils import find_wsi_file
from gaelo_pathology_processing.services.file_helper import get_file, move_to_storage, get_hash
from openslide import (OpenSlide)
import json
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class WsiMetadata(APIView):
    """Get WSI metadata"""

    def get(self, request : Request, id : str):
        try:
            wsi_file_path = find_wsi_file(id)
            if not wsi_file_path:
                return Response({f"No WSI files found for ID {id}"}, status=404)
            
            slide = OpenSlide(wsi_file_path)
            properties = slide.properties
            
            return Response(properties, status=200)
            
        except Exception as e:

            return Response({"error": "Failed to retrieve metadata"}, status=400)
            
