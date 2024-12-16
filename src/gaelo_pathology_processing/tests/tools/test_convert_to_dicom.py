from django.test import TestCase
import os, base64, unittest

from gaelo_pathology_processing.services.file_helper import move_to_storage


class TestConvertToDicom(TestCase):

    def setUp(self):
        credentials = base64.b64encode(b'GaelO:GaelO')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials.decode('utf-8')
        self.valid_payload = {
            "dicom_tags_study": {
                "PatientID": "123456",
                "PatientName": "patientName",
                "StudyDescription": "",
                "StudyID": "4569852",
                "SeriesNumber": "1",
                "AccessionNumber": "123456789",
                "Manufacturer": "",
                "FocusMethod": "AUTO",
                "ExtendedDepthOfField": "NO",
                "ImageType": "ORIGINAL\\SECONDARY\\VOLUME\\NONE",
                "SpecimenDescriptionSequence": [
                    {
                        "SpecimenIdentifier": "Specimen^Identifier",
                        "SpecimenUID": "1.2.276.0.7230010.3.1.4.3252829876.4112.1426166133.871",
                        "IssuerOfTheSpecimenIdentifierSequence": [],
                        "SpecimenPreparationSequence": []
                    }
                ]
            },
            "slides": [
                {"dicom_tags_series": {
                    "SeriesDescription": "Serie description",
                },
                    "wsi_id": "a38c8a8f747e3858c615614e4e0f6d30",

                },
                {"dicom_tags_series": {
                    "SeriesDescription": "Serie description",
                },
                    "wsi_id": "b3a10b48bd26c96df930e7b2ecf0a9a4",
                }

            ]
        }
    @unittest.skip('skip')

    def test_convert_to_dicom(self):

        test_storage_path = os.path.join(
            os.getcwd(), 'gaelo_pathology_processing/tests/storage/wsi')
        move_to_storage('wsi', test_storage_path,
                        'a38c8a8f747e3858c615614e4e0f6d30')
        move_to_storage('wsi', test_storage_path,
                        'b3a10b48bd26c96df930e7b2ecf0a9a4')

        response = self.client.post(
            "/tools/conversion/", self.valid_payload, content_type="application/json")
        print(response.json())

        self.assertEqual(response.status_code, 200)
