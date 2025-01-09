import json
import subprocess
import os
import tempfile
import zipfile
import hashlib
import uuid
from pathlib import Path

from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.response import Response
from pydicom.uid import generate_uid

from gaelo_pathology_processing.services.file_helper import move_to_storage, get_file
from gaelo_pathology_processing.services.utils import body_to_dict


class ConvertToDicomView(APIView):

    def get_study_orthanc_id(self, patient_id, study_instance_uid) -> str:
        string_to_hash = str(patient_id) + '|' + str(study_instance_uid)
        myhash = hashlib.sha1(string_to_hash.encode('utf-8'))
        hash = myhash.hexdigest()
        hash = '-'.join(hash[i:i+8] for i in range(0, len(hash), 8))
        return hash

    def post(self, request: Request) -> Response:
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
                return Response({"error": "Patient ID is required."}, status=400)

            if not patient_name:
                return Response({"error": "Patient name is required."}, status=400)

            # Generate a study instance UID to make all series belongs to the same study
            study_instance_uid = generate_uid()
            number_of_all_instances = 0
            for slide in slides:

                # initialization of the dataset
                dicom_tags = initialize_dicom_tags(
                    study_instance_uid, data['dicom_tags_study'] | slide['dicom_tags_series'])
                wsi_id = slide['wsi_id']
                wsi_path = get_file('wsi', wsi_id)
                if not wsi_path:
                    return Response({"error": f"WSI file with ID '{wsi_id}' does not exist."}, status=404)

                with tempfile.TemporaryDirectory() as temp_dir:
                    dataset_path = Path(temp_dir) / 'dataset.json'
                    with open(dataset_path, 'w') as json_file:
                        json.dump(dicom_tags, json_file, indent=2)

                    output_dir = Path(temp_dir) / 'dicoms'
                    output_dir.mkdir(parents=True, exist_ok=True)

                    # conversion to DICOM
                    result = convert_to_dicom(
                        wsi_path, output_dir, wsi_id, dataset_path)

                    # zip of DICOM folder
                    zip_file_name = f"{study_instance_uid}.zip"
                    zip_temp_path = Path(temp_dir) / zip_file_name
                    number_of_instances = zip_dicom(result, zip_temp_path)
                    number_of_all_instances = number_of_all_instances + number_of_instances

                    # move zip into storage
                    move_to_storage('dicoms', zip_temp_path, zip_file_name)

            study_orthanc_id = self.get_study_orthanc_id( patient_id, study_instance_uid)
            return Response({"study_instance_uid": study_instance_uid, 'study_orthanc_id': study_orthanc_id,  'number_of_instances': number_of_all_instances}, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON."}, status=400)
        except KeyError as e:
            return Response({"error": f"Missing key: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


def initialize_dicom_tags(study_instance_uid, data):
    """Initialize the DICOM tags dataset."""

    if not isinstance(data, dict):  # Vérifie si 'data' est un dictionnaire
        raise ValueError("Expected a dictionary, got None or an invalid type.")
    return {
        "PatientID": data.get('PatientID'),
        "PatientName": data.get('PatientName'),
        "StudyInstanceUID": study_instance_uid,
        "StudyDescription": data.get('StudyDescription'),
        "StudyID": data.get('StudyID'),
        "AccessionNumber": data.get('AccessionNumber', "GaelO"),
        "SeriesInstanceUID": generate_uid(),
        "SeriesDescription": data.get('SeriesDescription', ''),
        "SeriesNumber": data.get("SeriesNumber", '1'),  # --> could be a string
        "Manufacturer": data.get('Manufacturer'),
        "ImageType": data.get('ImageType', "ORIGINAL\\SECONDARY"),
        "FocusMethod": data.get('FocusMethod', "AUTO"),
        "ExtendedDepthOfField": data.get('ExtendedDepthOfField', "NO"),
        "SpecimenDescriptionSequence": [
            {
                "SpecimenIdentifier": "Specimen^Identifier",
                "SpecimenUID": "1.2.276.0.7230010.3.1.4.3252829876.4112.1426166133.871",
                "IssuerOfTheSpecimenIdentifierSequence": [],
                "SpecimenPreparationSequence": []
            }
        ]
    }


def zip_dicom(folder_path: str, zip_path: str) -> int:
    """
    Creates a ZIP file containing all the contents of the specified folder.

    Args:
        folder_path (str): Path of the file to zip
        zip_path (str): Zip path
    """
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = Path(root) / file
                    destination_filename = str(uuid.uuid4())
                    zipf.write(file_path, arcname=destination_filename)
        return len(files)
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
        __file__), '..', '..', '..', '..', 'lib', 'OrthancWSIDicomizer')
    openslide_path = os.path.join(os.path.dirname(
        __file__), '..', '..', '..', '..', 'lib', 'libopenslide.so.0')

    command = [
        str(executable_path),
        "--openslide="+str(openslide_path),
        "--compression=jpeg",
        "--jpeg-quality=100",
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
