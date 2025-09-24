import os
from services.interfaces import BookMetadataProvider
from services.openlibrary import LocalOpenLibraryProvider
from services.internet_archive import LocalInternetArchiveProvider
from services.http_clients import RemoteOpenLibraryProvider, RemoteInternetArchiveProvider

def get_openlibrary_provider() -> BookMetadataProvider:
    if os.getenv("USE_REMOTE_PROVIDERS") == "true":
        return RemoteOpenLibraryProvider()
    return LocalOpenLibraryProvider()

def get_internet_archive_provider() -> BookMetadataProvider:
    if os.getenv("USE_REMOTE_PROVIDERS") == "true":
        return RemoteInternetArchiveProvider()
    return LocalInternetArchiveProvider()