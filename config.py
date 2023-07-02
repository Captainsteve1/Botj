import os
from dotenv import load_dotenv

if os.path.exists("config.env"):
    load_dotenv('config.env', override=True)

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "5984917620:AAGLPu49AqW5xf9JNAlNaLLf-wiggkE5vDo")
    API_ID = int(os.environ.get("API_ID", d94b3f7f51b7222dcc04b64f9d72eb4d))
    API_HASH = os.environ.get("API_HASH", "d94b3f7f51b7222dcc04b64f9d72eb4d")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://Devilharsha:Devilharsha@cluster0.exwkd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "6120738413").split(" ")] #  Owner Id
    OWNER_ID = [int(i) for i in  os.environ.get("OWNER_ID", "6046440697").split(" ")]
    OWNER_ID.append(1204927413)
    AUTH_USERS += OWNER_ID
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "")
