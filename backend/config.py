import os
from dotenv import load_dotenv
from pathlib import Path

# Tự động tìm file .env trong thư mục backend
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    SQL_SERVER = os.getenv('SQL_SERVER', 'localhost')
    SQL_DATABASE = os.getenv('SQL_DATABASE', 'learning_platform')
    SQL_USERNAME = os.getenv('SQL_USERNAME', 'sa')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD', 'YourStrongPassword')
    USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'False').lower() == 'true'
    SQL_DRIVER = os.getenv('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    if USE_WINDOWS_AUTH or (not SQL_USERNAME and not SQL_PASSWORD):
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{SQL_SERVER}/{SQL_DATABASE}"
            f"?driver={SQL_DRIVER.replace(' ', '+')}"
            f"&trusted_connection=yes"
            f"&charset=utf8"
            f"&encoding=utf8"
            f"&autocommit=True"
            f"&timeout=10"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}@{SQL_SERVER}/{SQL_DATABASE}"
            f"?driver={SQL_DRIVER.replace(' ', '+')}"
            f"&charset=utf8"
            f"&encoding=utf8"
            f"&autocommit=True"
            f"&timeout=10"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 10, "pool_recycle": 3600, "pool_pre_ping": True, "max_overflow": 20}
    
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 86400
    JWT_DECODE_ALGORITHMS = ['HS256']
    
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', 'ai_models/recommendation_model.h5')
    ENABLE_AI = os.getenv('ENABLE_AI', 'True').lower() == 'true'
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')