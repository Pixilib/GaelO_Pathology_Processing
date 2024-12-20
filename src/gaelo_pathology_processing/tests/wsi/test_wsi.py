from django.test import TestCase
import os, base64
from gaelo_pathology_processing.services.file_helper import move_to_storage
import unittest
class TestWsi(TestCase):

    def setUp(self):
        credentials = base64.b64encode(b'GaelO:GaelO')
        self.client.defaults['HTTP_AUTHORIZATION'] = 'Basic ' + credentials.decode('utf-8')

    def test_post_wsi(self):
        """Testing the POST request to retrieve a wsi image"""

        test_storage_path = os.path.join(os.getcwd(), 'gaelo_pathology_processing/tests/storage/wsi/')
        file_path = os.path.join(test_storage_path, 'images_wsi.zip')
        print(file_path)
        image = open(
            file_path, "rb"
        )

        response = self.client.post(
            "/wsi/",
            image.read(),
            content_type='application/octet-stream'
        )
            
        print("Response content:", response.content.decode())
        self.assertEqual(response.status_code, 200)

    def test_get_wsi(self):
        
        test_storage_path = os.getcwd() + '/gaelo_pathology_processing/tests/storage/wsi/b3a10b48bd26c96df930e7b2ecf0a9a4'
        move_to_storage('wsi', test_storage_path, 'b3a10b48bd26c96df930e7b2ecf0a9a4.zip')

        response = self.client.get('/wsi/b3a10b48bd26c96df930e7b2ecf0a9a4/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn(f'attachment; filename="b3a10b48bd26c96df930e7b2ecf0a9a4.zip"', response['Content-Disposition'])
        