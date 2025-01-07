from gaelo_pathology_processing.services.file_helper import get_file
from openslide import (OpenSlide)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class WsiMetadata(APIView):
    """Get WSI metadata"""

    def get(self, request : Request, id : str):
        try:
            wsi_file = get_file('wsi', id)
            if not wsi_file:
                return Response({f"No WSI files found for ID {id}"}, status=404)
            slide = OpenSlide(wsi_file.name)
            properties = slide.properties
            
            return Response(properties, status=200)
            
        except Exception as e:
            return Response({"error": "Failed to retrieve metadata"}, status=500)
            
