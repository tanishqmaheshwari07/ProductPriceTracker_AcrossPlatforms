import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Gemini API (Google)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')


    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')  # FIX #3: no hardcoded fallback — must be set via .env
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set. Add it to your .env file.")

    DEBUG = os.getenv('DEBUG', 'False') == 'True'  # FIX #4: default to False (safe for production)

    # Database Configuration
    database_url = os.getenv('DATABASE_URL', 'sqlite:///priceai.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress FSADeprecationWarning

    # Flask-Mail Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

