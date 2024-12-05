import hashlib
from django.core.files.storage import storages, Storage
from django.core.files.base import ContentFile
from typing import IO


def get_hash(path_to_tmp: str) -> str:
    hash = hashlib.md5(open(path_to_tmp, 'rb').read()).hexdigest()
    return hash

def __get_storage(storage_name: str) -> Storage:
    return storages[storage_name]

def store(storage_name: str, filename: str, payload: str) -> None:
    storage = __get_storage(storage_name)
    if (not storage.exists(filename)):
        storage.save(filename, ContentFile(payload))


def move_to_storage(storage_name: str, path_origin: str, filename: str) -> None:
    storage = __get_storage(storage_name)

    if (not storage.exists(filename)):
        storage.save(filename, open(path_origin, 'rb'))


def get_file(storage_name: str, filename: str) -> IO[any]:
    storage = __get_storage(storage_name)
    file = storage.open(filename, 'rb')
    return file


def is_file_exists(storage_name: str, filename: str) -> bool:
    storage = __get_storage(storage_name)
    return storage.exists(filename)

"""
lists file in a folder use path = '' to list file at the root 
and path = 'myfolder' to list file in a subdirectory
"""


def list_files(storage_name: str, path: str = '') -> tuple[list[str], list[str]]:
    storage = __get_storage(storage_name)
    return storage.listdir(path)


def delete_file(storage_name: str, filename: str) -> None:
    storage = __get_storage(storage_name)
    storage.delete(filename)


def get_path(storage_name: str, filename: str) -> str:
    storage = __get_storage(storage_name)
    return storage.path(filename)