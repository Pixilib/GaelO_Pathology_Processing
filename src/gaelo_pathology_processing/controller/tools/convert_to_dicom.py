import json
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

from gaelo_pathology_processing.services.abstractDicomizer import AbstractDicomizer
from gaelo_pathology_processing.services.file_helper import move_to_storage, get_file
from gaelo_pathology_processing.services.utils import body_to_dict, transcode_dicom_to_jpeg_lossless


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
            dicom_folders = []
            for slide in slides:
                # initialization of the dataset
                wsi_id = slide['wsi_id']
                wsi_path = get_file('wsi', wsi_id)
                if not wsi_path:
                    return Response({"error": f"WSI file with ID '{wsi_id}' does not exist."}, status=404)
                temp_dir_dicom = tempfile.TemporaryDirectory()

                # Mirax Management: if it is a folder, we pass the folder path
                if isinstance(wsi_path, str) and os.path.isdir(wsi_path):
                    mrxs_files = list(Path(wsi_path).glob("*.mrxs"))
                    if not mrxs_files:
                        return Response({"error": f"No .mrxs file found in {wsi_path}."}, status=400)
                    wsi_input = str(mrxs_files[0])
                else:
                    wsi_input = str(wsi_path)

                dicom_tags = data['dicom_tags_study'] | slide['dicom_tags_series']
                dicomizer = AbstractDicomizer.get_dicomizer(wsi_input)
                # conversion to DICOM
                dicomizer.convert(study_instance_uid, dicom_tags,
                                  wsi_input, temp_dir_dicom.name)
                # append temporary folder to folder array to fuse for generating dicom zip batch
                dicom_folders.append(temp_dir_dicom)

            # create final zip file
            zip_file_name = f"{study_instance_uid}.zip"
            zip_temp_file = tempfile.NamedTemporaryFile(
                mode="w+", suffix=zip_file_name)
            zip_file = zipfile.ZipFile(zip_temp_file.name, 'w')
            # compute number of instances
            number_of_all_instances = 0
            for dicom_folder in dicom_folders:
                # add all file in it (with uuid name)
                number_of_instances = add_files_to_zip(
                    dicom_folder.name, zip_file, False)
                number_of_all_instances = number_of_all_instances + number_of_instances
            zip_file.close()
            # move zip into storage
            move_to_storage('dicoms', zip_temp_file.name, zip_file_name)
            study_orthanc_id = self.get_study_orthanc_id(
                patient_id, study_instance_uid)
            return Response({"study_instance_uid": study_instance_uid, 'study_orthanc_id': study_orthanc_id,  'number_of_instances': number_of_all_instances}, status=200)

        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON."}, status=400)
        except KeyError as e:
            return Response({"error": f"Missing key: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


def add_files_to_zip(folder_path: str, zip_file: zipfile.ZipFile, compress_jpeg_ls=False) -> int:
    """
    Creates a ZIP file containing all the contents of the specified folder.

    Args:
        folder_path (str): Path of the file to zip
        zip_path (str): Zip path
    """
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            destination_filename = str(uuid.uuid4())
            if (compress_jpeg_ls):
                dicom_compressed_temp = tempfile.NamedTemporaryFile(mode="w+")
                transcode_dicom_to_jpeg_lossless(
                    file_path, dicom_compressed_temp.name)
                zip_file.write(dicom_compressed_temp.name,
                               arcname=destination_filename)
            else:
                zip_file.write(file_path, arcname=destination_filename)
    return len(files)
