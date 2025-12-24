import os
from app.books.helpers.book_metadata.bookmetdataprovider import BookMetadataProvider
from app.books.helpers.book_metadata.openlibrary import OpenLibraryProvider
from app.books.helpers.book_metadata.internet_archive import InternetArchiveProvider

def get_providers() -> list[BookMetadataProvider]:
    return [OpenLibraryProvider()
            # InternetArchiveProvider()
            ]
