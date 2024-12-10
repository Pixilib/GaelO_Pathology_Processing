from django.test import TestCase
import os

from gaelo_pathology_processing.services.file_helper import move_to_storage

class TestConvertToDicom(TestCase):

    def setUp(self):
        self.valid_payload ={
            "wsi_id": "751b0b86a3c5ff4dfc8567cf24daaa85",
            "dicom_tags": {
                "PatientID": "",
                "PatientName": "",
                "StudyID": "",
                "SeriesNumber": "1",
                "AccessionNumber": "123456789",
                "ImageType" : "DERIVED\\PRIMARY\\VOLUME\\NONE",
                "Manufacturer": "",
                "FocusMethod": "AUTO",
                "ExtendedDepthOfField": "NO",
                "SpecimenDescriptionSequence": [
                {
                    "SpecimenIdentifier": "Specimen^Identifier",
                    "SpecimenUID": "1.2.276.0.7230010.3.1.4.3252829876.4112.1426166133.871",
                    "IssuerOfTheSpecimenIdentifierSequence": [],
                    "SpecimenPreparationSequence": []
                }
                ]
            }
        }



    def test_convert_to_dicom(self):

        test_storage_path = os.path.join(os.getcwd(), 'gaelo_pathology_processing/tests/storage/wsi/751b0b86a3c5ff4dfc8567cf24daaa85.zip')
        move_to_storage('wsi', test_storage_path, '751b0b86a3c5ff4dfc8567cf24daaa85.zip')


        response = self.client.post("/tools/conversion/", self.valid_payload, content_type="application/json")
        print(response.json()) 

        self.assertEqual(response.status_code, 200) 

