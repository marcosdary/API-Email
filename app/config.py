from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from enum import Enum

load_dotenv()

# Credencias do APP
class Config(Enum):
    USERNAME = getenv("USERNAME")
    PASSWORD = getenv("PASSWORD")
    SMTP_SERVER = getenv("SMTP_SERVER")
    SMTP_PORT = getenv("SMTP_PORT")
    SMTP_USERNAME = getenv("SMTP_USERNAME")
    SMTP_PASSWORD = "pwum lvva rvyw zhah"  
    SENDER = SMTP_USERNAME
    HTML_FILE_PATH = Path(__file__).parent / "templates" / "email" / "notification_email.html"
    PATH_LOGGING = Path(__file__).parent.parent / "logs" / "log.json"
    PATH_LOGGING_NUVEM = "/users.json"
    PATH_TEST_FILE = Path(__file__).parent.parent / "tests" / "file"


