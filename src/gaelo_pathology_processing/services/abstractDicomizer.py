import os
import json
import shutil
import tempfile, zipfile
import subprocess
from abc import ABC, abstractmethod
from openslide import OpenSlide
from pydicom import Dataset
from pydicom.uid import generate_uid

from wsidicomizer.metadata import WsiDicomizerMetadata
from wsidicomizer import WsiDicomizer
from wsidicom.metadata import (
    Equipment,
    Patient,
    Series,
    Study,
)
from wsidicom.codec import JpegSettings, Subsampling, JpegLosslessSettings
from gaelo_pathology_processing.services.utils import get_wsi_format


class AbstractDicomizer(ABC):

    @classmethod
    def get_dicomizer(cls, image_path: str):
       
        image_format = get_wsi_format(image_path)
        print(f"Detected image format: {image_format}")
        if image_format == 'leica' or image_format == 'isyntax':
            big_picture = BigPictureDicomizer()
            return big_picture
        else:
            orthanc = OrthancDicomizer()
            return orthanc

    def convert(self, study_instance_uid, metadata, image_path, output_path): 
        self.initialize_dicoms_tags(study_instance_uid, metadata)
        
        if zipfile.is_zipfile(image_path):
            temp_dir = tempfile.mkdtemp()
            try:
                with zipfile.ZipFile(image_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                # Search for file to open with OpenSlide in the extracted files (some format has splits in part files)
                slide_file = None
                for f in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, f)
                    if os.path.isfile(file_path) and OpenSlide.detect_format(file_path) is not None:
                        slide_file = file_path
                        break
                if not slide_file:
                    raise ValueError("No file compatible with OpenSlide found in the zip archive.")
                self.convert_to_dicom(slide_file, output_path)
            finally:
                shutil.rmtree(temp_dir)
        else:
            self.convert_to_dicom(image_path, output_path)

    @abstractmethod
    def convert_to_dicom(self, image_path :str, output_path :str):
        pass

    @abstractmethod
    def initialize_dicoms_tags(self, study_instance_uid :str, metadata :dict):
        pass


class OrthancDicomizer(AbstractDicomizer):

    wsi_metadata: dict

    def write_json_file(self, dicom_tags: dict):
        # create json dataset for dicom metadata
        temp_json = tempfile.NamedTemporaryFile(mode="w+", suffix='.json')
        json.dump(dicom_tags, temp_json)
        temp_json.flush()
        return temp_json

    def convert_to_dicom(self, image_path, output_path):
        """
            Converts an image to a DICOM file using OrthancWSIDicomizer.

            Args:
                image_path (str): Path of image
                base_output_dir (str): Path of the output directory (after conversion)
                wsi_id (str): ID of the wsi image to convert
                dataset_path (str): Path of the dataset.json for the dicoms tags
        """
        executable_path = os.path.join(os.path.dirname(
            __file__), '..', '..', '..', 'lib', 'OrthancWSIDicomizer')
        openslide_path = os.path.join(os.path.dirname(
            __file__), '..', '..', '..', 'lib', 'libopenslide.so.1')

        metadata_path = self.write_json_file(self.wsi_metadata)

        command = [
            str(executable_path),
            "--openslide="+str(openslide_path),
            "--compression=jpeg",
            "--jpeg-quality=100",
            str(image_path),
            "--dataset="+metadata_path.name,
            "--folder",
            str(output_path),
            "--force-openslide", "1",
            "--max-size=10",
            "--levels=6",
            "--smooth=1"
        ]

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error converting to DICOM : {e}")

    def initialize_dicoms_tags(self, study_instance_uid :str, data :dict):
        """Initialize the DICOM tags dataset."""

        if not isinstance(data, dict):  # Vérifie si 'data' est un dictionnaire
            raise ValueError(
                "Expected a dictionary, got None or an invalid type.")
        self.wsi_metadata = {
            "PatientID": data.get('PatientID'),
            "PatientName": data.get('PatientName'),
            "StudyInstanceUID": study_instance_uid,
            "StudyDescription": data.get('StudyDescription'),
            "StudyID": data.get('StudyID'),
            "AccessionNumber": data.get('AccessionNumber', "GaelO"),
            "SeriesInstanceUID": generate_uid(),
            "SeriesDescription": data.get('SeriesDescription', ''),
            # --> could be a string
            "SeriesNumber": data.get("SeriesNumber", '1'),
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


class BigPictureDicomizer(AbstractDicomizer):

    wsi_metadata: WsiDicomizerMetadata

    def convert_to_dicom(self, image_path :str, output_path :str):
        """
            Converts an image to a DICOM file using big_picture.
            Args:
                image_path (str): Path of image
                base_output_dir (str): Path of the output directory (after conversion)
                wsi_id (str): ID of the wsi image to convert
                dataset_path (str): Path of the dataset.json for the dicoms tags
        """
        os.makedirs(output_path, exist_ok=True)

        try:

            subsampling = Subsampling.from_string("420")
            encoding_settings = JpegSettings(
                quality=100, subsampling=subsampling
            )
            #encoding_settings = JpegLosslessSettings()
        
            # Déterminer les paramètres pour les niveaux en fonction des propriétés du WSI
            with WsiDicomizer.open(image_path, self.wsi_metadata) as wsi:
                total_levels = len(wsi.levels)
                print(f"Total levels in WSI: {total_levels}")
                if total_levels < 6:
                    # If less than 6 levels, add the missing ones to reach 6 levels (0-5)
                    add_missing_levels_param = True
                    include_levels_param = list(range(6)) 
                else:  # total_levels >= 6
                    # If 6 or more levels, take the first 6 levels
                    add_missing_levels_param = False
                    include_levels_param = list(range(6))
        
            WsiDicomizer.convert(
                filepath= image_path,
                output_path= output_path,
                metadata = self.wsi_metadata,
                encoding = encoding_settings,
                include_label=False,
                include_overview=False,
                include_thumbnail=False,
                include_confidential=True,
                add_missing_levels=add_missing_levels_param,
                include_levels=include_levels_param,
                
            )
        except Exception as e:
            raise Exception(f"Error converting to DICOM : {e}")

    def initialize_dicoms_tags(self, study_instance_uid :str, data :dict) -> WsiDicomizerMetadata:
        """Initialize the DICOM tags dataset for Big Picture dicomizer."""
        if not isinstance(data, dict):
            raise ValueError(
                "Expected a dictionary, got None or an invalid type.")

        study = Study(identifier=data.get('StudyID'), uid=study_instance_uid,
                      accession_number=data.get('AccessionNumber'))
        series = Series(number=int(data.get('SeriesNumber', '1')))
        patient = Patient(name=data.get('PatientName'))
        equipment = Equipment(
            manufacturer=data.get('Manufacturer')
        )

        # series_extra_tags_dataset = Dataset()
        # series_description = data.get('SeriesDescription', '')
        # if series_description:
        #     series_extra_tags_dataset.SeriesDescription = series_description

        metadata = WsiDicomizerMetadata(
            study=study,
            series=series,
            patient=patient,
            equipment=equipment,
            #merge=[series_extra_tags_dataset] if series_extra_tags_dataset else None
        )

        self.wsi_metadata = metadata
