import os
from dotenv import load_dotenv

if os.path.exists("config.env"):
    load_dotenv('config.env', override=True)

class Config:
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "5876669861:AAFY1HCsYM_Sj2G_L86wBHqcq0XdF8R9y-g")
    API_ID = int(os.environ.get("API_ID", 15855531))
    API_HASH = os.environ.get("API_HASH", "31e0b87de4285ebff259e003f58bf469")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://Devilharsha:Devilharsha@cluster0.exwkd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "6120738413").split(" ")] #  Owner Id
    OWNER_ID = [int(i) for i in  os.environ.get("OWNER_ID", "6046440697").split(" ")]
    OWNER_ID.append(1204927413)
    AUTH_USERS += OWNER_ID
    GDRIVE_FOLDER_NAME = os.environ.get("GDRIVE_FOLDER_NAME", "AMAZON_DL")
    INDEX_URL = os.environ.get("INDEX_URL", "https://amazondl.herokuapp.com")
