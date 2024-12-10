from pathlib import Path
import shutil
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
import tempfile
import zipfile
import os
from gaelo_pathology_processing.services.file_helper import move_to_storage, get_hash

class WsiView(APIView):
    """
    Upload a wsi image
    """
    def post(self, request : Request):
        try:
            binary_data = request.body
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
                temp_zip.write(binary_data)
                temp_zip_path = temp_zip.name

            if not zipfile.is_zipfile(temp_zip_path):
                return Response({'error': 'The file sent is not a valid ZIP.'}, status=400)

            # Unzip the ZIP into a temporary directory
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                extract_dir = Path(tempfile.mkdtemp())
                zip_ref.extractall(extract_dir)

            # Browse extracted files, process them and move them
            files = []
            for file_path in extract_dir.iterdir():
                if file_path.is_file():
                    file_hash = get_hash(file_path)
                    file_name = f"{file_hash}{file_path.suffix}"
                    move_to_storage('wsi', str(file_path), file_name)
                    files.append(file_name)

            os.remove(temp_zip_path)
            shutil.rmtree(extract_dir)

            return Response({
                'message': 'ZIP unzipped and files stored successfully.',
                'files': files
            }, status=200)

        except Exception as e:
            return Response({'error': f'{str(e)}'}, status=500)

