import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

# Automatically find and load the root .env file
root_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=root_env_path, override=True)

class Settings(BaseModel):
    # App Information
    APP_NAME: str = "FRIDAY AI Assistant"
    VERSION: str = "0.1.0"
    
    # Server Networking
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Active LLM Provider
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq") # groq, ollama, mock
    
    # Groq Primary & Fallbacks
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODELS: str = os.getenv("GROQ_FALLBACK_MODELS", "llama-3.1-8b-instant,mixtral-8x7b-32768,gemma2-9b-it")
    
    # Ollama Local Settings
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # Voice Settings
    WAKE_WORD: str = os.getenv("WAKE_WORD", "FRIDAY")
    MIC_RECORD_DURATION_SECONDS: int = int(os.getenv("MIC_RECORD_DURATION_SECONDS", "7"))
    TTS_VOICE_RATE: int = int(os.getenv("TTS_VOICE_RATE", "190"))

settings = Settings()
