from django.test import TestCase
import os
from rest_framework.request import Request
from rest_framework.response import Response
from django.core.files.uploadedfile import SimpleUploadedFile



class TestWsi(TestCase):
    def test_post_wsi(self):
        """Testing the POST request to retrieve a wsi image"""

        test_storage_path = os.path.join(os.getcwd(), 'gaelo_pathology_processing/tests/storage/wsi/')
        file_path = os.path.join(test_storage_path, 'CMU-2.zip')

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