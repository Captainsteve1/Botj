from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import pickle
import magic
from config import Config
import logging

logging.basicConfig(level=logging.INFO)

async def get_gdrive_service():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/drive']
    try:
        creds = service_account.Credentials.from_service_account_file('credentials.json')
    except Exception:
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
    return build('drive', 'v3', credentials=creds)

async def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type

async def create_directory(directory_name):
    service = await get_gdrive_service()
    file_metadata = {
            "name": directory_name,
            "mimeType": "application/vnd.google-apps.folder",
	    'parents': [Config.GDRIVE_FOLDER_ID]
        }
    file = service.files().create(supportsTeamDrives=True, body=file_metadata).execute()
    file_id = file.get("id")
    return file_id


async def GdriveUploader(file_path, parent_id=None):
    service = await get_gdrive_service()
    file_name = os.path.basename(file_path)
    mime_type = await get_mime_type(file_path)
    if parent_id == None:
        parent_id = Config.GDRIVE_FOLDER_ID
    file_metadata = {
		'name': file_name,
		'description': 'Shared By @shelltony1bot',
		'mimeType': mime_type,
		'parents': [parent_id]
	}
    media = MediaFileUpload(file_path, resumable=True, mimetype=mime_type, chunksize=70 * 1024 * 1024)
    file = service.files().create(supportsTeamDrives=True,
                                  body=file_metadata,
                                  media_body=media,
				  fields='id').execute()
    try:
        file_url = f"https://drive.google.com/open?id={file.get('id')}"
        return True, file_url
    except Exception as e:
        return False, file
