from django.test import TestCase
from gaelo_pathology_processing.services.abstractDicomizer import AbstractDicomizer, OrthancDicomizer, BigPictureDicomizer
from wsidicomizer.metadata import WsiDicomizerMetadata
from pathlib import Path
import os
from gaelo_pathology_processing.services.file_helper import move_to_storage, get_file
import tempfile
from wsidicom.metadata import (
    Equipment,
    Patient,
    Series,
    Study,
)
class TestAbstractDicomizer(TestCase):
    
    def setUp(self):
        self.test_storage_path_wsi = Path(os.getcwd(), 'gaelo_pathology_processing', 'tests', 'storage', 'wsi')
        move_to_storage('wsi', str(self.test_storage_path_wsi) + '/a38c8a8f747e3858c615614e4e0f6d30','a38c8a8f747e3858c615614e4e0f6d30') #aperio
        move_to_storage('wsi', str(self.test_storage_path_wsi) + '/b3a10b48bd26c96df930e7b2ecf0a9a4','b3a10b48bd26c96df930e7b2ecf0a9a4') #None
        self.wsi_path_aperio = get_file('wsi', 'a38c8a8f747e3858c615614e4e0f6d30')
        self.wsi_path_jpeg = get_file('wsi', 'b3a10b48bd26c96df930e7b2ecf0a9a4')
        self.temp_output_dir = tempfile.mkdtemp()
   
    def test_get_dicomizer(self):
        dicomizer = AbstractDicomizer.get_dicomizer(self.wsi_path_aperio.name)
        self.assertIsInstance(dicomizer, BigPictureDicomizer)

        dicomizer = AbstractDicomizer.get_dicomizer(self.wsi_path_jpeg.name)
        self.assertIsInstance(dicomizer, OrthancDicomizer)

    
    def test_orthanc_convert_to_dicom(self):
        dicomizer = OrthancDicomizer()
        dicomizer.wsi_metadata = {
            'PatientID': '123',
            'PatientName': 'John Doe',
            'StudyID': '456',
            'AccessionNumber': '789',
            'SeriesDescription': 'Test Series',
            'Manufacturer': 'Test Manufacturer'
        }
        dicomizer.convert_to_dicom(self.wsi_path_jpeg.name, self.temp_output_dir)

        output_files = os.listdir(self.temp_output_dir)
        self.assertTrue(output_files)

    def test_orthanc_initialize_dicoms_tags(self):
        dicomizer = OrthancDicomizer()
        metadata = {
            'PatientID': '123',
            'PatientName': 'John Doe',
            'StudyID': '456',
            'AccessionNumber': '789',
            'SeriesDescription': 'Test Series',
            'Manufacturer': 'Test Manufacturer'
        }

        dicomizer.initialize_dicoms_tags('uid', metadata)
        self.assertEqual(dicomizer.wsi_metadata['PatientID'], '123')
        self.assertEqual(dicomizer.wsi_metadata['PatientName'], 'John Doe')

    def test_big_picture_convert_to_dicom(self):
        dicomizer = BigPictureDicomizer()
        dicomizer.wsi_metadata = WsiDicomizerMetadata(
            study=Study(identifier='456'), series=Series(number=1), patient=Patient(name='John Doe'), equipment=Equipment(manufacturer='manufacturer')
        )
        dicomizer.convert_to_dicom(self.wsi_path_aperio.name, self.temp_output_dir)
        output_files = os.listdir(self.temp_output_dir)
        self.assertTrue(output_files)

    def test_big_picture_initialize_dicoms_tags(self):
        dicomizer = BigPictureDicomizer()
        metadata = {
            'PatientName': 'John Doe',
            'StudyID': '456',
            'AccessionNumber': '789',
            'SeriesNumber': '1',
            'Manufacturer': 'Test Manufacturer'
        }
        dicomizer.initialize_dicoms_tags('uid', metadata)
        self.assertEqual(dicomizer.wsi_metadata.patient.name, 'John Doe')
