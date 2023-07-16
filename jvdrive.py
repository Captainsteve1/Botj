#!/usr/bin/env python3
from logging import getLogger, ERROR
from time import time
from pickle import load as pload
from os import path as ospath, listdir, remove as osremove
from re import search as re_search
from urllib.parse import parse_qs, urlparse
from random import randrange
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError
from asyncio import sleep
import magic
from util import humanbytes, TimeFormatter, setInterval
from config import Config

GLOBAL_EXTENSION_FILTER = (".aria", ".aria2c")
LOGGER = getLogger(__name__)

getLogger('googleapiclient.discovery').setLevel(ERROR)


class GdriveStatus:
    def __init__(self, obj):
        self.__obj = obj
        self.__size = obj.total_size
        self.message = obj.message

    async def update(self):
        if self.__obj.done:
            return
        try:
            text=f'''**Name:** `{self.name()}`
**Progress:** `{self.progress()}`
**Downloaded:** `{self.processed_bytes()}`
**Total Size:** `{self.size()}`
**Speed:** `{()}`
**ETA:** `{self.eta()}`
**Engine:** `Google Drive`'''
            await self.message.edit(text=text)
        except Exception as e:
            LOGGER.error(e, exc_info=True)

    def processed_bytes(self):
        return humanbytes(self.__obj.processed_bytes)
    
    def size(self):
        return humanbytes(self.__size)
    
    def name(self):
        return self.__obj.name

    def progress_raw(self):
        try:
            return self.__obj.processed_bytes / self.__size * 100
        except:
            return 0
    
    def progress(self):
        return f'{round(self.progress_raw(), 2)}%'

    def speed(self):
        return f'{humanbytes(self.__obj.speed)}/s'
    
    def eta(self):
        try:
            seconds = (self.__size - self.__obj.processed_bytes) / \
                self.__obj.speed
            return TimeFormatter(seconds)
        except:
            return '-'
    
    def download(self):
        return self.__obj

class GoogleDriveHelper:

    def __init__(self, name=None, path=None, bot_loop=None, message=None):
        self.__OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
        self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
        self.__G_DRIVE_BASE_DOWNLOAD_URL = "https://drive.google.com/uc?id={}&export=download"
        self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = "https://drive.google.com/drive/folders/{}"
        self.__path = path
        self.__total_bytes = 0
        self.__total_files = 0
        self.__total_folders = 0
        self.__processed_bytes = 0
        self.__total_time = 0
        self.__start_time = 0
        self.__alt_auth = False
        self.__is_uploading = False
        self.__is_cancelled = False
        self.__is_errored = False
        self.__status = None
        self.__updater = None
        self.__update_interval = 5
        self.__sa_index = 0
        self.__sa_count = 1
        self.__sa_number = 100
        self.__service = self.__authorize()
        self.__file_processed_bytes = 0
        self.__processed_bytes = 0
        self.bot_loop = bot_loop
        self.message = message
        self.name = name
        self.done = False

    @property
    def speed(self):
        try:
            return self.__processed_bytes / self.__total_time
        except:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    def __authorize(self):
        credentials = None
        if Config.USE_SERVICE_ACCOUNTS:
            json_files = listdir("accounts")
            self.__sa_number = len(json_files)
            self.__sa_index = randrange(self.__sa_number)
            LOGGER.info(
                f"Authorizing with {json_files[self.__sa_index]} service account")
            credentials = service_account.Credentials.from_service_account_file(
                f'accounts/{json_files[self.__sa_index]}',
                scopes=self.__OAUTH_SCOPE)
        elif ospath.exists('token.pickle'):
            LOGGER.info("Authorize with token.pickle")
            with open('token.pickle', 'rb') as f:
                credentials = pload(f)
        else:
            LOGGER.error('token.pickle not found!')
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def __alt_authorize(self):
        if not self.__alt_auth:
            self.__alt_auth = True
            if ospath.exists('token.pickle'):
                LOGGER.info("Authorize with token.pickle")
                with open('token.pickle', 'rb') as f:
                    credentials = pload(f)
                return build('drive', 'v3', credentials=credentials, cache_discovery=False)
            else:
                LOGGER.error('token.pickle not found!')
        return None

    def __switchServiceAccount(self):
        if self.__sa_index == self.__sa_number - 1:
            self.__sa_index = 0
        else:
            self.__sa_index += 1
        self.__sa_count += 1
        LOGGER.info(f"Switching to {self.__sa_index} index")
        self.__service = self.__authorize()

    def get_mime_type(self, file_path):
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        mime_type = mime_type or "text/plain"
        return mime_type

    @staticmethod
    def __getIdFromUrl(link):
        if "folders" in link or "file" in link:
            regex = r"https:\/\/drive\.google\.com\/(?:drive(.*?)\/folders\/|file(.*?)?\/d\/)([-\w]+)"
            res = re_search(regex, link)
            if res is None:
                raise IndexError("G-Drive ID not found.")
            return res.group(3)
        parsed = urlparse(link)
        return parse_qs(parsed.query)['id'][0]

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(Exception))
    def __set_permission(self, file_id):
        permissions = {
            'role': 'reader',
            'type': 'anyone',
            'value': None,
            'withLink': True
        }
        return self.__service.permissions().create(fileId=file_id, body=permissions, supportsAllDrives=True).execute()


    async def progress_show(self):
        if self.__status is not None:
            chunk_size = self.__status.total_size * \
                self.__status.progress() - self.__file_processed_bytes
            self.__file_processed_bytes = self.__status.total_size * self.__status.progress()
            self.__processed_bytes += chunk_size
            self.__total_time += self.__update_interval
            progress__ = GdriveStatus(self)
            await progress__.update()

    def deletefile(self, link: str):
        try:
            file_id = self.__getIdFromUrl(link)
        except (KeyError, IndexError):
            return "Google Drive ID could not be found in the provided link"
        msg = ''
        try:
            self.__service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            msg = "Successfully deleted"
            LOGGER.info(f"Delete Result: {msg}")
        except HttpError as err:
            if "File not found" in str(err) or "insufficientFilePermissions" in str(err):
                token_service = self.__alt_authorize()
                if token_service is not None:
                    LOGGER.error('File not found. Trying with token.pickle...')
                    self.__service = token_service
                    return self.deletefile(link)
                err = "File not found or insufficientFilePermissions!"
            LOGGER.error(f"Delete Result: {err}")
            msg = str(err)
        return msg

    def upload(self, file_name, size):
        self.__is_uploading = True
        item_path = f"{self.__path}/{file_name}"
        LOGGER.info(f"Uploading: {item_path}")
        self.total_size = size
        self.__updater = setInterval(self.__update_interval, self.progress_show, self.bot_loop)
        try:
            if ospath.isfile(item_path):
                if item_path.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                    raise Exception('This file extension is excluded by extension filter!')
                mime_type = self.get_mime_type(item_path)
                link = self.__upload_file(
                    item_path, file_name, mime_type, Config.GDRIVE_FOLDER_ID, is_dir=False)
                if self.__is_cancelled:
                    return
                if link is None:
                    raise Exception('Upload has been manually cancelled')
                LOGGER.info(f"Uploaded To G-Drive: {item_path}")
            else:
                mime_type = 'Folder'
                dir_id = self.__create_directory(ospath.basename(
                    ospath.abspath(file_name)), Config.GDRIVE_FOLDER_ID)
                result = self.__upload_dir(item_path, dir_id)
                if result is None:
                    raise Exception('Upload has been manually cancelled!')
                link = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)
                if self.__is_cancelled:
                    return
                LOGGER.info(f"Uploaded To G-Drive: {file_name}")
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(
                    f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            self.__is_errored = True
            raise Exception(err)
        finally:
            self.__updater.cancel()
            if self.__is_cancelled and not self.__is_errored:
                if mime_type == 'Folder':
                    LOGGER.info("Deleting uploaded data from Drive...")
                    link = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)
                    self.deletefile(link)
                return
            elif self.__is_errored:
                return
            self.done = True
            return (link, size, self.__total_files, mime_type, file_name)

    def __upload_dir(self, input_directory, dest_id):
        list_dirs = listdir(input_directory)
        if len(list_dirs) == 0:
            return dest_id
        new_id = None
        for item in list_dirs:
            current_file_name = ospath.join(input_directory, item)
            if ospath.isdir(current_file_name):
                current_dir_id = self.__create_directory(item, dest_id)
                new_id = self.__upload_dir(current_file_name, current_dir_id)
                self.__total_folders += 1
            elif not item.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                mime_type = self.get_mime_type(current_file_name)
                file_name = current_file_name.split("/")[-1]
                # current_file_name will have the full path
                self.__upload_file(current_file_name,
                                   file_name, mime_type, dest_id)
                self.__total_files += 1
                new_id = dest_id
            else:
                osremove(current_file_name)
                new_id = 'filter'
            if self.__is_cancelled:
                break
        return new_id

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(Exception))
    def __create_directory(self, directory_name, dest_id):
        file_metadata = {
            "name": directory_name,
            "description": "Uploaded by Mirror-leech-telegram-bot",
            "mimeType": self.__G_DRIVE_DIR_MIME_TYPE
        }
        if dest_id is not None:
            file_metadata["parents"] = [dest_id]
        file = self.__service.files().create(
            body=file_metadata, supportsAllDrives=True).execute()
        file_id = file.get("id")
        if not Config.IS_TEAM_DRIVE:
            self.__set_permission(file_id)
        LOGGER.info(
            f'Created G-Drive Folder:\nName: {file.get("name")}\nID: {file_id}')
        return file_id

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=(retry_if_exception_type(Exception)))
    def __upload_file(self, file_path, file_name, mime_type, dest_id, is_dir=True):
        # File body description
        file_metadata = {
            'name': file_name,
            'description': 'Uploaded by bot',
            'mimeType': mime_type,
        }
        if dest_id is not None:
            file_metadata['parents'] = [dest_id]

        if ospath.getsize(file_path) == 0:
            media_body = MediaFileUpload(file_path,
                                         mimetype=mime_type,
                                         resumable=False)
            response = self.__service.files().create(body=file_metadata, media_body=media_body,
                                                     supportsAllDrives=True).execute()
            if not Config.IS_TEAM_DRIVE:
                self.__set_permission(response['id'])

            drive_file = self.__service.files().get(
                fileId=response['id'], supportsAllDrives=True).execute()
            return self.__G_DRIVE_BASE_DOWNLOAD_URL.format(drive_file.get('id'))
        media_body = MediaFileUpload(file_path,
                                     mimetype=mime_type,
                                     resumable=True,
                                     chunksize=100 * 1024 * 1024)

        # Insert a file
        drive_file = self.__service.files().create(
            body=file_metadata, media_body=media_body, supportsAllDrives=True)
        response = None
        retries = 0
        while response is None and not self.__is_cancelled:
            try:
                self.__status, response = drive_file.next_chunk()
            except HttpError as err:
                if err.resp.status in [500, 502, 503, 504] and retries < 10:
                    retries += 1
                    continue
                if err.resp.get('content-type', '').startswith('application/json'):
                    reason = eval(err.content).get(
                        'error').get('errors')[0].get('reason')
                    if reason not in [
                        'userRateLimitExceeded',
                        'dailyLimitExceeded',
                    ]:
                        raise err
                    if Config.USE_SERVICE_ACCOUNTS:
                        if self.__sa_count >= self.__sa_number:
                            LOGGER.info(
                                f"Reached maximum number of service accounts switching, which is {self.__sa_count}")
                            raise err
                        else:
                            if self.__is_cancelled:
                                return
                            self.__switchServiceAccount()
                            LOGGER.info(f"Got: {reason}, Trying Again.")
                            return self.__upload_file(file_path, file_name, mime_type, dest_id)
                    else:
                        LOGGER.error(f"Got: {reason}")
                        raise err
        if self.__is_cancelled:
            return
        try:
            osremove(file_path)
        except:
            pass
        self.__file_processed_bytes = 0
        # Insert new permissions
        if not Config.IS_TEAM_DRIVE:
            self.__set_permission(response['id'])
        # Define file instance and get url for download
        if not is_dir:
            drive_file = self.__service.files().get(
                fileId=response['id'], supportsAllDrives=True).execute()
            return self.__G_DRIVE_BASE_DOWNLOAD_URL.format(drive_file.get('id'))
        return
