from pathlib import Path
import shutil
import tempfile
import zipfile
import os
from openslide import (OpenSlide)
from django.http import FileResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from gaelo_pathology_processing.services.utils import get_wsi_format
from ...exceptions import GaelONotFoundException
from gaelo_pathology_processing.services.file_helper import get_file, move_to_storage, get_hash, is_file_exists, delete_file


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

            if zipfile.is_zipfile(temp_file_path):
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    with tempfile.TemporaryDirectory() as extract_dir:
                        zip_ref.extractall(extract_dir)
                        # Search for .mrxs and associated folder
                        mrxs_path = None
                        dat_folder = None
                        for root, dirs, files in os.walk(extract_dir):
                            for file in files:
                                if file.lower().endswith('.mrxs'):
                                    mrxs_path = Path(root) / file
                                    mrxs_stem = mrxs_path.stem
                                    # Look for the folder with the same name as the .mrxs
                                    for r2, d2, f2 in os.walk(extract_dir):
                                        for d in d2:
                                            if d == mrxs_stem:
                                                candidate = Path(r2) / d
                                                if list(candidate.glob('*.dat')):
                                                    dat_folder = candidate
                                                    break
                                    break
                            if mrxs_path and dat_folder:
                                break
                        if not mrxs_path or not dat_folder:
                            return Response({'error': 'No .mrxs file or .dat folder found in zip'}, status=400)
                        
                        with tempfile.TemporaryDirectory() as flat_dir:
                            # Copy .mrxs
                            flat_mrxs = Path(flat_dir) / mrxs_path.name
                            flat_mrxs.write_bytes(mrxs_path.read_bytes())
                            # Copy the .dat folder
                            flat_dat_folder = Path(flat_dir) / dat_folder.name
                            shutil.copytree(dat_folder, flat_dat_folder)
                 
                            file_hash = get_hash(flat_mrxs)
                            format_wsi = get_wsi_format(flat_mrxs)
                            if format_wsi is None:
                                return Response({'error': 'Invalid file or unsupported format'}, status=400)

                            # Create the destination folder
                            storage_dir = Path('storage/wsi') / file_hash
                            storage_dir.mkdir(parents=True, exist_ok=True)

                            shutil.copy2(flat_mrxs, storage_dir / flat_mrxs.name)

                            # Copy the .dat folder into this folder
                            shutil.copytree(flat_dat_folder, storage_dir / flat_dat_folder.name, dirs_exist_ok=True)

                            mrxs_file = storage_dir / flat_mrxs.name

                            return Response({'id': file_hash, 'mrxs_path': str(mrxs_file)}, status=200)
            
            else:
                file_hash = get_hash(temp_file_path)
                format_wsi = get_wsi_format(Path(temp_file_path))
                if format_wsi is None:
                    return Response({'error': 'Invalid file or unsupported format'}, status=400)
                move_to_storage('wsi', str(temp_file_path), file_hash)
                return Response({'id': file_hash}, status=200)

        except Exception as e:
            return Response({'error': f'{str(e)}'}, status=500)

    def get(self, request: Request, id: str):
        try:
            file = get_file('wsi', id)
            response = FileResponse(file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{id}"'
            response['Content-Type'] = 'application/octet-stream'

            return response
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        

    def delete(self, request : Request, id : str):
        if not is_file_exists('wsi', id):
            raise GaelONotFoundException("File doesn't exist")
        delete_file('wsi', id)
        return Response(status=200)
