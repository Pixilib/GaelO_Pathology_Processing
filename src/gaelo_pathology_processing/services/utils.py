import json, os

from gaelo_pathology_processing.services.file_helper import get_path, list_files


def body_to_dict(body :str) -> dict:
    body_unicode = body.decode('utf-8')
    dict = json.loads(body_unicode)
    return dict
