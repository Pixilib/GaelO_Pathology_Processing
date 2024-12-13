import json
import os

from gaelo_pathology_processing.services.file_helper import get_path, list_files


def body_to_dict(body :str) -> dict:
    body_unicode = body.decode('utf-8')
    dict = json.loads(body_unicode)
    return dict

def find_wsi_file(wsi_id: str):
    """
    Search for a wsi file by its ID in the storage and return its path

    Args:
        wsi_id (str): wsi image id
    Returns:
        str: path of file found
    """
    dirs, files = list_files('wsi', '')
    for filename in files:
        if os.path.splitext(filename)[0] == wsi_id:
            return get_path('wsi', filename)
    return None
