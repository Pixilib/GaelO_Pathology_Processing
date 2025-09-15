from django.test import TestCase
import os, base64
from gaelo_pathology_processing.services.file_helper import move_to_storage
class TestDicom(TestCase):

    def setUp(self):
        credentials = base64.b64encode(b'GaelO:GaelO')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials.decode('utf-8')

    def test_get_zip_dicom(self):
        """Testing the GET request to retrieve a DICOM image as a zip"""

        id = "5c1c5278-5229-4511-8878-1d671826c773"
        test_storage_path = os.getcwd() + '/gaelo_pathology_processing/tests/storage/dicom/test_dicom.zip'
        move_to_storage('dicoms', test_storage_path, id + '.zip')

        response = self.client.get('/dicom/'+ id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn(f'attachment; filename="{id}.zip"', response['Content-Disposition'])


    def test_delete_zip_dicom(self):
        test_storage_path = os.getcwd() + '/gaelo_pathology_processing/tests/storage/dicom/test_dicom_delete.zip'        
        move_to_storage('dicoms', test_storage_path, 'test_dicom_delete.zip')
        response = self.client.delete('/dicom/'+ 'test_dicom_delete.zip')
        self.assertEqual(response.status_code, 200)

