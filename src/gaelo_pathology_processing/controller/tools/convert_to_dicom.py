from rest_framework.request import Request
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import subprocess
import os
import tempfile
import zipfile
from pathlib import Path
from gaelo_pathology_processing.services.file_helper import get_path, list_files, move_to_storage
from gaelo_pathology_processing.services.utils import body_to_dict


class ConvertToDicomView(APIView):

    def post(self, request: Request) -> HttpResponse:
        """
        Converts an image to a DICOM file, zips and sends to storage
        """
        try:
            data = body_to_dict(request.body)
            wsi_id = data.get('wsi_id')
            dicom_tags = data.get('dicom_tags')

            if not wsi_id:
                return Response({"error": "The WSI image ID is required."}, status=400)

            if not dicom_tags:
                return Response({"error": "Dicom tags are required."})

            # Image data required to read the dicom in the OHIF viewer
            image_type = data.get('dicom_tags', {}).get('ImageType', [])
            image_type_values = image_type.split('\\')
            if not image_type or len(image_type_values) < 2:
                return Response({"error": "The typical image must contain at least two values ​​(Pixel Data and Examination Characteristics)"}, status=400)

            valid_values_value1 = ['ORIGINAL', 'DERIVED']
            valid_values_value2 = ['PRIMARY', 'SECONDARY']
            if image_type_values[0] not in valid_values_value1:
                return Response({"error": "The first value of ImageType must be 'ORIGINAL' or 'DERIVED'"}, status=400)

            if image_type_values[1] not in valid_values_value2:
                return Response({"error": "The second value of ImageType must be 'PRIMARY' or 'SECONDARY'"}, status=400)

            # initialization of the dataset
            dataset_path = './storage/wsi/dataset.json'
            with open(dataset_path, 'w') as json_file:
                json.dump(dicom_tags, json_file, indent=2)

            with open(dataset_path, 'r') as json_file:
                json_content = json.load(json_file)

            wsi_path = find_wsi_file(wsi_id)
            if not wsi_path:
                return Response({"error": f"WSI file with ID '{wsi_id}' does not exist."}, status=404)

            with tempfile.TemporaryDirectory() as temp_dir:
                base_output_dir = Path(temp_dir) / 'dicoms'
                base_output_dir.mkdir(parents=True, exist_ok=True)

                # conversion to DICOM
                result = convert_to_dicom(
                    wsi_path, base_output_dir, wsi_id, dataset_path)

                # zip of DICOM folder
                zip_file_name = f"{wsi_id}.zip"
                zip_temp_path = Path(temp_dir) / zip_file_name
                zip_dicom(result, zip_temp_path)

                # move zip into storage
                move_to_storage('dicoms', zip_temp_path, zip_file_name)

                return Response({"message": "Conversion successful and DICOM folder moved on storage !", "dataset": json_content}, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


def find_wsi_file(wsi_id: str):
    """
    Search for a wsi file by its ID in the storage and return its path

    Args:
        wsi_id (str): wsi image id
    Returns:
        str: path of file found
    """
    dirs, files = list_files('wsi', '')
    for filename in files:
        if os.path.splitext(filename)[0] == wsi_id:
            return get_path('wsi', filename)
    return None


def zip_dicom(folder_path : str, zip_path : str):
    """
    Creates a ZIP file containing all the contents of the specified folder.

    Args:
        folder_path (str): Path of the file to zip
        zip_path (str): Zip path
    """
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Parcourir tous les fichiers et dossiers dans le dossier
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file
                    print(f"Added file {file_path} to the archive.")
                    zipf.write(file_path, arcname=arcname)
            print(f"ZIP créé : {zip_path}")
    except Exception as e:
        print(f"Error creating zip : {e}")


def convert_to_dicom(image_path: str, base_output_dir: str, wsi_id: str, dataset_path: str) -> str:
    """
    Converts an image to a DICOM file using OrthancWSIDicomizer.

    Args:
        image_path (str): Path of image
        base_output_dir (str): Path of the output directory (after conversion)
        wsi_id (str): ID of the wsi image to convert
        dataset_path (str): Path of the dataset.json for the dicoms tags
    """
    output_dir = Path(base_output_dir) / wsi_id
    os.makedirs(output_dir, exist_ok=True)
    executable_path = os.path.join(os.path.dirname(
        __file__), '..', '..', '..', '..', 'OrthancWSIDicomizer-2.1.exe')

    # Commande OrthancWSIDicomizer
    command = [
        executable_path,
        "--openslide=libopenslide-1.dll",
        image_path,
        "--dataset="+dataset_path,
        "--folder",
        output_dir
    ]

    try:
        subprocess.run(command, check=True)
        return base_output_dir
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting to DICOM : {e}")
