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

    # Database Configuration — FIX #5: was missing entirely, causing Flask-SQLAlchemy to crash
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///priceai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress FSADeprecationWarning
