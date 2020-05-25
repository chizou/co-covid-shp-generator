# My final final project!
# Adam Chou
# This application connects to Google Drive to download the Colorado COVID-19
# case data from https://drive.google.com/drive/folders/1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1.
# The application then processes the county specific data into the attribute table of a
# Colorado by county shapefile

from __future__ import print_function
import os
import io
import yaml
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaIoBaseDownload

class GDriveDownloader:
    def __init__(self, api_key, download_dir="downloads", parent_id="1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1"):
        self._download_dir = download_dir
        self._parent_id = parent_id
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        self._service = build('drive', 'v3', developerKey=api_key)

    def download(self):
        # filter the GDrive query to only query the CO Covid drive and only csv or google sheet files
        parent_id = "1bBAC7H-pdEDgPxRuU_eR36ghzc0HWNf1"
        query = f"'{parent_id}' in parents and (mimeType contains 'text/csv')"

        page_token = None
        while True:
            # Get the list of files from the CO Covid G-Drive.
            list_request = self._service.files().list(
                q=query,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                #fields="*", # for debug purposes
                fields="nextPageToken, files(id, name, mimeType)",
                spaces='drive',
                ).execute()

            for file in list_request.get('files', []):
                print(file)
                file_request = self._service.files().get_media(fileId=file['id'])
                filename = f"{self._download_dir}/{file['name']}"
                fh = io.FileIO(filename, 'wb')
                downloader = MediaIoBaseDownload(fh, file_request)
                done = False
                while done is False:
                    try:
                        status, done = downloader.next_chunk()
                        print("Download %d%%." % int(status.progress() * 100))
                    except HttpError as e:
                        print(e)
                        done = True


            # continue to get files if we exceed page size
            page_token = list_request.get('nextPageToken', None)
            if page_token is None:
                break