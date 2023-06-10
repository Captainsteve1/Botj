from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
from google.oauth2 import service_account
import os
import pickle
#import magic
import mimetypes
from config import Config
import logging

import shutil
import requests
from time import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from util import humanbytes, get_video_duration
from pathlib import Path
import asyncio
import re
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

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
    #mime = magic.Magic(mime=True)
    #mime_type = mime.from_file(file_path)
    #mime_type = mime_type or "text/plain"
    mime_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
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

async def upload_to_gdrive(file_upload, message):
    del_it = await message.reply_text(
            f"Now Uploading to google drive☁️!!!"
        )
    if not os.path.exists("rclone.conf"):
        return await del_it.edit("Please ask owner to setup gdrive configs first")
    if os.path.exists("rclone.conf"):
        with open("rclone.conf", "r+") as file:
            con = file.read()
            gUP = re.findall("\[(.*)\]", con)[0]
    file_upload = str(Path(file_upload).resolve())
    LOGGER.info(file_upload)
    is_file = os.path.isfile(file_upload)
    destination = Config.GDRIVE_FOLDER_NAME
    if not is_file:
        destination = os.path.join(destination, os.path.basename(file_upload))
    cmd = [
            "rclone",
            "copy",
            "--config=rclone.conf",
            f"{file_upload}",
            f"{gUP}:{destination}",
            "-v",
        ]
    LOGGER.info(cmd)
    tmp = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    pro, cess = await tmp.communicate()
    LOGGER.info(cess.decode("utf-8"))
    _file = re.escape(os.path.basename(file_upload))
    LOGGER.info(_file)
    filter_file = f"filter_{time()}.txt"
    with open(filter_file, "w+", encoding="utf-8") as filter:
        print(f"+ {_file}\n- *", file=filter)
    t_a_m = [
            "rclone",
            "lsf",
            "--config=rclone.conf",
            "-F",
            "i",
            f"--filter-from={filter_file}",
            "--files-only" if is_file else "--dirs-only",
            f"{gUP}:{destination}",
        ]
    jigar_proc = await asyncio.create_subprocess_exec(
            *t_a_m, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    jv, jig = await jigar_proc.communicate()
    file_id = jv.decode().strip()
    LOGGER.info(jig.decode())
    os.remove(filter_file)
    driveURL = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
    size = humanbytes(os.path.getsize(file_upload))
    if Config.INDEX_LINK:
        indexURL = f"{Config.INDEX_LINK}/{os.path.basename(file_upload)}{'/' if not is_file else ''}"
        indexURL = requests.utils.requote_uri(indexURL)
    else:
        indexURL = driveURL
    if is_file:
        duration = await get_video_duration(file_upload)
    else:
        duration = len(os.listdir(file_upload))
    await message.reply_text(
            f"🤖 File: `{os.path.basename(file_upload)}`\n📀 Size: {size}\n{'Duration:' if is_file else 'Episodes:'} {duration}\n\n[Drive link]({driveURL}) | [index link]({indexURL})",
        )
    if is_file:
        os.remove(file_upload)
    else:
        shutil.rmtree(file_upload)
    await del_it.delete()
    