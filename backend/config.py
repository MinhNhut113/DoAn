import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SQL Server Configuration
    SQL_SERVER = os.getenv('SQL_SERVER', 'localhost')
    SQL_DATABASE = os.getenv('SQL_DATABASE', 'learning_platform')
    SQL_USERNAME = os.getenv('SQL_USERNAME', 'sa')
    SQL_PASSWORD = os.getenv('SQL_PASSWORD', 'YourStrongPassword')
    USE_WINDOWS_AUTH = os.getenv('USE_WINDOWS_AUTH', 'False').lower() == 'true'
    
    # SQL Server Connection String with optimization
    if USE_WINDOWS_AUTH or (not SQL_USERNAME and not SQL_PASSWORD):
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{SQL_SERVER}/{SQL_DATABASE}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
            f"&trusted_connection=yes"
            f"&timeout=10"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}@{SQL_SERVER}/{SQL_DATABASE}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
            f"&timeout=10"
        )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "max_overflow": 20,
    }
    
    # JWT Configuration
    # NOTE: Do NOT use hard-coded defaults for secrets in production.
    # Read from environment variables; if missing, application should warn/fail fast in production.
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_DECODE_ALGORITHMS = ['HS256']
    
    # Flask Configuration
    # IMPORTANT: set `SECRET_KEY` via environment variable in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # AI Configuration
    AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', 'ai_models/recommendation_model.h5')
    ENABLE_AI = os.getenv('ENABLE_AI', 'True').lower() == 'true'

