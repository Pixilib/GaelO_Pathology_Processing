from django.test import TestCase
from unittest.mock import MagicMock, Mock, patch
from gaelo_pathology_processing.services.abstractDicomizer import AbstractDicomizer, OrthancDicomizer, BigPictureDicomizer
from wsidicomizer.metadata import WsiDicomizerMetadata

class TestAbstractDicomizer(TestCase):
    
    @patch('gaelo_pathology_processing.services.abstractDicomizer.openslide.OpenSlide.detect_format')
    @patch('gaelo_pathology_processing.services.abstractDicomizer.is_isyntax')
    def test_get_dicomizer(self, mock_is_isyntax, mock_detect_format):
        mock_detect_format.return_value = 'aperio'
        dicomizer = AbstractDicomizer.get_dicomizer('image_path')
        self.assertIsInstance(dicomizer, BigPictureDicomizer)

        mock_detect_format.return_value = 'unknown_format'
        mock_is_isyntax.return_value = False
        dicomizer = AbstractDicomizer.get_dicomizer('image_path')
        self.assertIsInstance(dicomizer, OrthancDicomizer)

    @patch.object(OrthancDicomizer, 'convert_to_dicom')
    @patch.object(OrthancDicomizer, 'initialize_dicoms_tags')
    def test_convert(self, mock_initialize_dicoms_tags, mock_convert_to_dicom):
        dicomizer = OrthancDicomizer()
        dicomizer.convert('uid', {}, 'image_path', 'output_path')
        mock_initialize_dicoms_tags.assert_called_once_with('uid', {})
        mock_convert_to_dicom.assert_called_once_with('image_path', 'output_path')

    @patch('gaelo_pathology_processing.services.abstractDicomizer.subprocess.run')
    @patch('gaelo_pathology_processing.services.abstractDicomizer.tempfile.NamedTemporaryFile')
    def test_orthanc_convert_to_dicom(self, mock_tempfile, mock_subprocess_run):
        dicomizer = OrthancDicomizer()
        dicomizer.wsi_metadata = {}
        mock_tempfile.return_value_name = 'metadata_path'
        dicomizer.convert_to_dicom('image_path', 'output_path')
        mock_subprocess_run.assert_called_once()


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

    @patch('gaelo_pathology_processing.services.abstractDicomizer.WsiDicomizer.convert')
    def test_big_picture_convert_to_dicom(self, mock_convert):
        dicomizer = BigPictureDicomizer()
        dicomizer.wsi_metadata = MagicMock(spec=WsiDicomizerMetadata)
        dicomizer.convert_to_dicom('image_path', 'output_path')
        mock_convert.assert_called_once_with('image_path', 'output_path', dicomizer.wsi_metadata)


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
