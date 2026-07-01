import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24  # 24h — fine for a hackathon demo

    NOMBA_CLIENT_ID = os.environ.get("NOMBA_CLIENT_ID")
    NOMBA_CLIENT_SECRET = os.environ.get("NOMBA_CLIENT_SECRET")
    NOMBA_SUBACCOUNT_ID = os.environ.get("NOMBA_SUBACCOUNT_ID")
    NOMBA_PARENT_ACCOUNT_ID = os.environ.get("NOMBA_PARENT_ACCOUNT_ID")
    NOMBA_BASE_URL = os.environ.get("NOMBA_BASE_URL", "https://sandbox.nomba.com")