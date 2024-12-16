import json, subprocess, os, tempfile, zipfile
from pathlib import Path

from rest_framework.request import Request
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from pydicom.uid import generate_uid

from gaelo_pathology_processing.services.file_helper import get_path, list_files, move_to_storage
from gaelo_pathology_processing.services.utils import body_to_dict, find_wsi_file


class ConvertToDicomView(APIView):

    def post(self, request: Request) -> HttpResponse:
        """
        Converts an image to a DICOM file, zips and sends to storage
        """
        try:
            data = body_to_dict(request.body)
            requested_dicom_tags = data.get('dicom_tags_study')
            patient_id = requested_dicom_tags.get('PatientID')
            patient_name = requested_dicom_tags.get('PatientName')

            slides = data.get('slides', [])

            if not slides or not all('wsi_id' in slide for slide in slides):
                return Response({"error": "Each slide must contain a 'wsi_id'."}, status=400)

            if not requested_dicom_tags:
                return Response({"error": "Dicom tags are required."}, status=400)

            if not patient_id:
                return Response({"error": "Patient ID is required." }, status=400)
            
            if not patient_name:
                return Response({"error": "Patient name is required."}, status=400)
            

            # Image data required to read the dicom in the OHIF viewer
            image_type = data.get('dicom_tags_study', {}).get(
                'ImageType', ['ORIGINAL', 'SECONDARY'])
            if not image_type or len(image_type) < 2:
                return Response({"error": "The typical image must contain at least two values ​​(Pixel Data and Examination Characteristics)"}, status=400)

            # initialization of the dataset
            dicom_tags = initialize_dicom_tags(data)
            results = []
            for slide in slides:
                wsi_id = slide['wsi_id']
                wsi_path = find_wsi_file(wsi_id)
                if not wsi_path:
                    return Response({"error": f"WSI file with ID '{wsi_id}' does not exist."}, status=404)

                with tempfile.TemporaryDirectory() as temp_dir:
                    dataset_path = Path(temp_dir)/ 'dataset.json'
                    with open(dataset_path, 'w') as json_file:
                        json.dump(dicom_tags, json_file, indent=2)

                    output_dir = Path(temp_dir) / 'dicoms'
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # conversion to DICOM
                    result = convert_to_dicom(
                        wsi_path, output_dir, wsi_id, dataset_path)

                    # zip of DICOM folder
                    zip_file_name = f"{wsi_id}.zip"
                    zip_temp_path = Path(temp_dir) / zip_file_name
                    zip_dicom(result, zip_temp_path)

                    # move zip into storage
                    move_to_storage('dicoms', zip_temp_path, zip_file_name)
                    results.append({"slide_id": wsi_id, "status": "success"})
                    print(results)
            return Response({"message": "Conversion successful and DICOM folder moved on storage !", "dataset": json.dumps(dicom_tags)}, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

def initialize_dicom_tags(data):
    """Initialize the DICOM tags dataset."""
    return {
        "PatientID": data['dicom_tags_study']['PatientID'],
        "PatientName": data['dicom_tags_study']['PatientName'],
        "StudyInstanceUID": generate_uid(),
        "StudyDescription": data['dicom_tags_study']['StudyDescription'],
        "AccessionNumber": data.get('dicom_tags_study', {}).get('AccessionNumber', "GaelO"),
        "SeriesInstanceUID": generate_uid(),
        "SeriesDescription": data['slides'][0]['dicom_tags_series']["SeriesDescription"],
        "StudyID": data['dicom_tags_study']['StudyID'],
        "SeriesNumber": data.get('dicom_tags_study', {}).get('SeriesNumber', 1),
        "Manufacturer": data.get('dicom_tags_study', {}).get('Manufacturer', ""),
        "ImageType": data['dicom_tags_study']['ImageType'],
        "FocusMethod": data.get('dicom_tags_study', {}).get('FocusMethod', "AUTO"),
        "ExtendedDepthOfField": data.get('dicom_tags_study', {}).get('ExtendedDepthOfField', "NO"),
        "SpecimenDescriptionSequence": [
            {
                "SpecimenIdentifier": "Specimen^Identifier",
                "SpecimenUID": "1.2.276.0.7230010.3.1.4.3252829876.4112.1426166133.871",
                "IssuerOfTheSpecimenIdentifierSequence": [],
                "SpecimenPreparationSequence": []
            }
        ]
    }

# def find_wsi_file(wsi_id: str):
#     """
#     Search for a wsi file by its ID in the storage and return its path

#     Args:
#         wsi_id (str): wsi image id
#     Returns:
#         str: path of file found
#     """
#     dirs, files = list_files('wsi', '')
#     for filename in files:
#         if os.path.splitext(filename)[0] == wsi_id:
#             return get_path('wsi', filename)
#     return None


def zip_dicom(folder_path: str, zip_path: str):
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
        __file__), '..', '..', '..', '..', 'OrthancWSIDicomizer')

    # Commande OrthancWSIDicomizer
    command = [
        str(executable_path),
        "--openslide=libopenslide-1.dll",
        str(image_path),
        "--dataset="+str(dataset_path),
        "--folder",
        str(output_dir)
    ]

    try:
        subprocess.run(command, check=True)
        return base_output_dir
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting to DICOM : {e}")
