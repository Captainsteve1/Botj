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
from util import humanbytes, get_video_duration, TimeFormatter, get_path_size
from pathlib import Path
import asyncio
import re

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
            f"**Uploading {os.path.basename(file_upload)} to google drive☁️!!!**"
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
            #"-P",
            "--config=rclone.conf",
            "--retries",
            "15",
            f"{file_upload}",
            f"{gUP}:{destination}",
            #"-vv",
            "-P"
        ]
    cmd = f"rclone copy --config=rclone.conf --retries 30 {file_upload} {gUP}:{destination} -v -P"
    LOGGER.info(cmd)
    process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    data = ""
    blank = 0
    comp = "▪️"
    ncomp = "▫️"
    while True:
        try:
            data  = await process.stdout.read()
            data = data.decode("utf-8").strip()
        except Exception as e:
            LOGGER.error(e)
            data = ""
        if data == "":
            blank += 1
        if blank == 30:
            break
        mat = re.findall("Transferred:.*ETA.*",data)
        if mat is not None and len(mat) > 0:
            try:
                prg = ""
                nstr = mat[0].replace("Transferred:","")
                nstr = nstr.strip()
                nstr = nstr.split(",")
                prg = nstr[1].strip("% ")
                pr = ""
                try:
                    percentage=int(prg)
                except:
                    percentage = 0
                for i in range(1,11):
                    if i <= int(percentage/10):
                        pr += comp
                    else:
                        pr += ncomp
                count += 1
                progress = "<b>Uploading:</b> {}%\n[{}]\n{} \n<b>Speed:</b> {} \n<b>ETA:</b> {}".format(prg,pr,nstr[0].replace("ytes","").replace("/","of"),nstr[2].replace("ytes",""),nstr[3].replace("ETA",""))
                if count >= 4:
                    count = 0
                    try:
                        await del_it.edit(text=progress,parse_mode="html")
                        await asyncio.sleep(7)
                    except:
                        pass
            except:
                pass
        else:
            continue
    await process.wait()
    LOGGER.info((await process.stderr.read()))
    _file = re.escape(os.path.basename(file_upload))
    LOGGER.info(_file)
    filter_file = f"filter_{time()}.txt"
    with open(filter_file, "w+", encoding="utf-8") as filter:
        print(f"+ {_file}\n- *", file=filter)
    t_a_m = [
            "rclone",
            "lsf",
            "--config=rclone.conf",
            "-R",
            "-F",
            "i",
            f"--filter-from={filter_file}",
            "--files-only" if is_file else "--dirs-only",
            f"{gUP}:{destination if is_file else Config.GDRIVE_FOLDER_NAME}",
        ]
    jigar_proc = await asyncio.create_subprocess_exec(
            *t_a_m, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
    jv, jig = await jigar_proc.communicate()
    file_id = jv.decode().strip().split(" ")[0].split("\n")[0]
    LOGGER.info(jig.decode())
    os.remove(filter_file)
    if not is_file:
        driveURL = f"https://drive.google.com/folderview?id={file_id}"
    else:
        driveURL = f"https://drive.google.com/file/d/{file_id}/view?usp=drivesdk"
    size = humanbytes(get_path_size(file_upload))
    if Config.INDEX_LINK:
        indexURL = f"{Config.INDEX_LINK}/{os.path.basename(file_upload)}{'/' if not is_file else ''}"
        indexURL = requests.utils.requote_uri(indexURL)
    else:
        indexURL = driveURL
    if is_file:
        duration = await get_video_duration(file_upload)
        duration = TimeFormatter(duration*1000)
    else:
        duration = len(os.listdir(file_upload))
    await message.reply_text(
            f"**Filename**: `{os.path.basename(file_upload)}`\n**Size**: `{size}`\n{'**Duration**:' if is_file else '**Episodes**:'} `{duration}`\n\n[Drive link]({driveURL}) | [index link]({indexURL})",
        )
    if is_file:
        os.remove(file_upload)
    else:
        shutil.rmtree(file_upload)
    await del_it.delete()
    
