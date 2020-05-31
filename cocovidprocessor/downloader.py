from __future__ import print_function

import io
import os
from glob import glob

from apiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class Downloader:
    def __init__(
        self,
        api_key,
        data_dir="downloads",
        parent_id="1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1",
    ):
        self._data_dir = data_dir
        self.__parent_id = parent_id
        if not os.path.exists(data_dir):
            os.mkdir(data_dir)
        self._service = build("drive", "v3", developerKey=api_key)

    def _get_file_list(self):
        os.chdir(self._data_dir)
        self._file_list = glob("*.csv")
        os.chdir("..")

    # Downloads files from the COVID data drive
    # refresh - specify whether to redownload files or skip files if they already exist
    def download(self, refresh=False, verbose=False):
        # filter the GDrive query to only query the CO Covid drive and only csv or google sheet files
        query = f"'{self.__parent_id}' in parents and (mimeType contains 'text/csv')"

        if not refresh:
            self._get_file_list()
        page_token = None

        while True:
            # Get the list of files from the CO Covid G-Drive.
            list_request = (
                self._service.files()
                .list(
                    q=query,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                    # fields="*", # for debug purposes
                    fields="nextPageToken, files(id, name, mimeType)",
                    spaces="drive",
                )
                .execute()
            )

            for file in list_request.get("files", []):
                if not refresh and file["name"] in self._file_list:
                    if verbose:
                        print(f"Skipping {file['name']}, already exists")
                    continue

                if verbose:
                    print(f"Downloading {file['name']}")
                file_request = self._service.files().get_media(fileId=file["id"])
                filename = f"{self._data_dir}/{file['name']}"
                fh = io.FileIO(filename, "wb")
                downloader = MediaIoBaseDownload(fh, file_request)
                done = False
                while done is False:
                    try:
                        status, done = downloader.next_chunk()
                        if verbose:
                            print("Download %d%%." % int(status.progress() * 100))
                    except HttpError as e:
                        print(e)
                        done = True

            # continue to get files if we exceed page size
            page_token = list_request.get("nextPageToken", None)
            if page_token is None:
                break
