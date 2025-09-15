from django.test import TestCase
import os, base64
from pathlib import Path
from gaelo_pathology_processing.services.file_helper import move_to_storage


class TestConvertToDicom(TestCase):

    def setUp(self):
        credentials = base64.b64encode(b'GaelO:GaelO')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + \
            credentials.decode('utf-8')
        self.valid_payload = {
            "dicom_tags_study": {
                "PatientID": "123456",
                "PatientName": "patientName",
                "StudyDescription": "",
                "StudyID": "4569852",
                "AccessionNumber": "123456789",
                "Manufacturer": "",
                "FocusMethod": "AUTO",
                "ExtendedDepthOfField": "NO",
                "ImageType": "",
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
                    "SeriesDescription": "Serie description 1",
                    "SeriesNumber": '1',

                },
                    "wsi_id": "a38c8a8f747e3858c615614e4e0f6d30",

                },
                # {"dicom_tags_series": {
                #     "SeriesDescription": "Serie description 2",
                #     "SeriesNumber": '2',

                # },
                #     "wsi_id": "1fb05ba18518cef86cfeac1123322933",
                # },
                # {"dicom_tags_series": {
                #     "SeriesDescription": "Serie description 3",
                #     "SeriesNumber": '3',

                # },
                #     "wsi_id": "86bed2d21e61b7062c9a8aecba077f6d",
                # },

                #  {"dicom_tags_series": {
                #     "SeriesDescription": "Serie description 4",
                #     "SeriesNumber": '4',

                # },
                #     "wsi_id": "d762ed9e13d4c47549672a54777f40e3",
                # }

            ]
        }

    def test_convert_to_dicom(self):

        test_storage_path = Path(os.getcwd(), 'gaelo_pathology_processing', 'tests', 'storage', 'wsi')
        move_to_storage('wsi', str(test_storage_path) + '/a38c8a8f747e3858c615614e4e0f6d30',
                        'a38c8a8f747e3858c615614e4e0f6d30') #aperio
        # move_to_storage('wsi', str(test_storage_path) + '/1fb05ba18518cef86cfeac1123322933',
        #                 '1fb05ba18518cef86cfeac1123322933') #philips TIFF 
        # move_to_storage('wsi', str(test_storage_path) + '/86bed2d21e61b7062c9a8aecba077f6d',
        #                 '86bed2d21e61b7062c9a8aecba077f6d') #ndpi 
        # move_to_storage('wsi', str(test_storage_path) + '/d762ed9e13d4c47549672a54777f40e3',
        #                 'd762ed9e13d4c47549672a54777f40e3') #isyntax 

        response = self.client.post(
            "/tools/conversion", self.valid_payload, content_type="application/json")

        self.assertEqual(response.status_code, 200)


