import os
from dotenv import load_dotenv

if os.path.exists("config.env"):
    load_dotenv('config.env', override=True)

class Config(object):
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "5984917620:AAGLPu49AqW5xf9JNAlNaLLf-wiggkE5vDo")
    API_ID = int(os.environ.get("API_ID", 15855531))
    API_HASH = os.environ.get("API_HASH", "31e0b87de4285ebff259e003f58bf469")
    DB_URL = os.environ.get("DB_URL", "mongodb+srv://Devilharsha:Devilharsha@cluster0.exwkd.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "6046440697").split(" ")] #  Owner Id
    OWNER_ID = [int(i) for i in  os.environ.get("OWNER_ID", "6046440697").split(" ")]
    OWNER_ID.append(1204927413)
    AUTH_USERS += OWNER_ID
    GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "18RuH2GB9uZX87FwsdJAIVZebozoXiSeQ")
    USE_SERVICE_ACCOUNTS = os.environ.get("USE_SERVICE_ACCOUNTS","")
    IS_TEAM_DRIVE = os.environ.get("IS_TEAM_DRIVE", "")
    INDEX_LINK = os.environ.get("INDEX_LINK", "https://t.tmirrorleech2993.workers.dev/0:/WEB-DL")
    #Zee5 token
    ZEE5_TOKEN = os.environ.get("ZEE5_TOKEN", "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImU2bF9sZjB4enBhWThXME1wVDNaUHM3aHI4RnhjS2tsOENXQlp6RUpPaUEifQ.eyJ1c2VyX2lkIjoiYmJmYzE0OTAtMTMxOC00OTVjLThjOGQtZDFmYzQ2MWE3ZDhlIiwiY3VycmVudF9jb3VudHJ5IjoiIiwicmVnaXN0cmF0aW9uX2NvdW50cnkiOiIiLCJhY3RpdmF0ZWQiOnRydWUsInN1YiI6IkJCRkMxNDkwLTEzMTgtNDk1Qy04QzhELUQxRkM0NjFBN0Q4RSIsImRldmljZV9pZCI6IiIsImlkcCI6ImxvY2FsIiwiY2xpZW50X2lkIjoicmVmcmVzaF90b2tlbiIsImF1ZCI6WyJ1c2VyYXBpIiwic3Vic2NyaXB0aW9uYXBpIiwicHJvZmlsZWFwaSJdLCJzY29wZSI6WyJ1c2VyYXBpIiwic3Vic2NyaXB0aW9uYXBpIiwicHJvZmlsZWFwaSJdLCJhbXIiOlsiZGVsZWdhdGlvbiJdLCJzdWJzY3JpcHRpb25zIjoiW10iLCJhY2Nlc3NfdG9rZW5fdHlwZSI6IkhpZ2hQcml2aWxlZ2UiLCJ2ZXJzaW9uIjoxLCJ1c2VyX3R5cGUiOiJSZWdpc3RlcmVkIiwidXNlcl9lbWFpbCI6ImdlZXJ2YW5pMjhAZ21haWwuY29tIiwidXNlcl9tb2JpbGUiOiI5MTk1MDI3NTEzNzMiLCJhdXRoX3RpbWUiOjE2Nzc4MTg1NjMsImV4cCI6MTY5MzU4NjU2MywiaWF0IjoxNjc3ODE4NTYzLCJpc3MiOiJodHRwczovL3VzZXJhcGkuemVlNS5jb20iLCJuYmYiOjE2Nzc4MTg1NjN9.YzJaDRGhPlHWNelvdiV_5b_KaxOFo39sGXEamMf3cMMbTPar5cMqvqcnoJVCdNVgRedKcOIZVXLuxSaSymmcoJWQEQnkYNuAEkVrChjzBaWljGs_v_KMlSuXSdztsS1-QBbyhjAcnK7qcFB8IVeR-ZWiO7tXm5ZwVUScQGV7HxfFvv9zuH03Ga3b4ES80ZQ9pP948HpTDvXy6pX4DiU2BKqDlKCOiYRFfbVOIrScNySLP_HNPcnVSKcm9K_E7RD4JZEjDa9tX_CyomK8fwMaR_fW0uUlfEKXT0BJLnt3U6HUrmrMfUcIBRojT7ewjwO-Bc6_ThizviWI8X7Szdgoxw")
    #Zee5 email pass
    ZEE5_EMAIL = os.environ.get("ZEE5_EMAIL", "geervani28@gmail.com")
    ZEE5_PASS = os.environ.get("ZEE5_PASS", "Race2002")
    #temp
    TEMP_DIR = os.environ.get("TEMP_DIR", "downloads")
