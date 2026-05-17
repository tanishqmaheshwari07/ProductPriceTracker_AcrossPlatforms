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
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-pro')
    
    # OpenAI API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
    
    # Claude API (Anthropic)
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-sonnet-20240229')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
