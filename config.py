import os
from dotenv import load_dotenv

if os.path.exists("config.env"):
    load_dotenv('config.env', override=True)

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "6048459549:AAHmy3Fnmo_8uNx6xf8EbcQWjkgFWen0Rig")
    API_ID = int(os.environ.get("API_ID", 15855531))
    API_HASH = os.environ.get("API_HASH", "31e0b87de4285ebff259e003f58bf469")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://Devilharsha:Devilharsha@cluster0.exwkd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "5561547043 -1001529582219 -1001663038905 1204927413").split(" ")] #  Owner Id
    OWNER_ID = [int(i) for i in  os.environ.get("OWNER_ID", "5561547043 1204927413").split(" ")]
    OWNER_ID.append(1204927413)
    AUTH_USERS += OWNER_ID
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "1PMk2D69Pe6eOn2UTMA5knfQc68HoEjY8")
