import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # AI API Configuration
    # Choose one: 'gemini', 'openai', or 'claude'
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')

    # Gemini API (Google)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')  # FIX #1: was 'gemini-pro' (deprecated)

    # OpenAI API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

    # Claude API (Anthropic)
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-5')  # FIX #2: was 'claude-3-sonnet-20240229' (deprecated)

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')  # FIX #3: no hardcoded fallback — must be set via .env
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set. Add it to your .env file.")

    DEBUG = os.getenv('DEBUG', 'False') == 'True'  # FIX #4: default to False (safe for production)

    # Database Configuration — FIX #5: was missing entirely, causing Flask-SQLAlchemy to crash
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///priceai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Suppress FSADeprecationWarning
