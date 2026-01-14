import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


def get_database_url():
    """Get database URL with SQLite fallback for development."""
    # Check for explicit DATABASE_URL first
    url = os.getenv('DATABASE_URL')
    if url:
        # Azure/Heroku sometimes use postgres:// instead of postgresql://
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        return url
    
    # Check for Azure SQL Server configuration
    sql_server = os.getenv('SQL_SERVER')
    sql_database = os.getenv('SQL_DATABASE')
    sql_user = os.getenv('SQL_USER')
    sql_password = os.getenv('SQL_PASSWORD')
    
    if sql_server and sql_database and sql_user and sql_password:
        # Azure SQL connection string using pyodbc
        params = quote_plus(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={sql_server};"
            f"DATABASE={sql_database};"
            f"UID={sql_user};"
            f"PWD={sql_password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
        )
        return f"mssql+pyodbc:///?odbc_connect={params}"
    
    # Default to SQLite for local development
    return 'sqlite:///studio_os.db'


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    
    # Twilio (WhatsApp)
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', '')
    
    # Email (SMTP)
    SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASS = os.getenv('SMTP_PASS', '')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'studio-os-assets')
    S3_BUCKET_URL = os.getenv('S3_BUCKET_URL', '')  # Public bucket URL or CDN URL
    
    # File Upload Limits
    MAX_IMAGE_SIZE = int(os.getenv('MAX_IMAGE_SIZE', 10 * 1024 * 1024))  # 10MB
    MAX_VIDEO_SIZE = int(os.getenv('MAX_VIDEO_SIZE', 100 * 1024 * 1024))  # 100MB
    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    ALLOWED_VIDEO_EXTENSIONS = ['mp4', 'mov', 'avi', 'webm']


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig,
}
