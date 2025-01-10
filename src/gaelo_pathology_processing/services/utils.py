import json
from pydicom import dcmread
from pydicom.filewriter import dcmwrite
from pydicom.uid import JPEGLSLossless


def body_to_dict(body: str) -> dict:
    body_unicode = body.decode('utf-8')
    dict = json.loads(body_unicode)
    return dict


def transcode_dicom_to_jpeg_lossless(input_path :str, output_path :str):
    # Read and return a dataset stored in accordance with the DICOM File Format
    dataset = dcmread(input_path)
    # compress in JpegLossless
    dataset.decompress()
    dataset.compress(JPEGLSLossless)
    # write the compressed Dicom File
    dcmwrite(output_path, dataset, enforce_file_format=False)
    return output_path
