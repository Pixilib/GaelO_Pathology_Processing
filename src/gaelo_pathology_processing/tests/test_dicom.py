from django.test import TestCase
from django.urls import reverse
import os

from gaelo_pathology_processing.services.file_helper import move_to_storage
class TestDicom(TestCase):

    def setUp(self):
        
        pass
       
    def test_post_convert_to_dicom_with_image(self):
        """Test de la requête POST pour convertir une image en DICOM et la récupère sous forme de ZIP"""

        test_storage_path = os.path.join(os.getcwd(), 'gaelo_pathology_processing/tests/storage/wsi/')
        file_path = os.path.join(test_storage_path, 'CMU-1.svs')
        
        with open(file_path, 'rb') as wsi_image:
            response = self.client.post(
                "/dicom/",
                {'image': wsi_image},
            )
        
        print("Response content:", response.content.decode())
        self.assertEqual(response.status_code, 200)

    def test_post_convert_to_dicom_image_not_found(self):
        """Test de la requête POST sans envoyer d'image"""

        response = self.client.post(
            "/dicom/",
            {'image': '' },
            )
        print("Response content:", response.content.decode())
        self.assertEqual(response.status_code, 400)
        

    def test_get_zip_dicom(self):
        """Test de la requête GET pour récupérer une image DICOM sous forme de zip"""

        id = "5c1c5278-5229-4511-8878-1d671826c773"
        test_storage_path = os.getcwd() + '/gaelo_pathology_processing/tests/storage/dicom/test_dicom.zip'
        move_to_storage('dicoms', test_storage_path, id + '.zip')

        url = reverse('get_dicom_zip', args=[id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn(f'attachment; filename="{id}.zip"', response['Content-Disposition'])

