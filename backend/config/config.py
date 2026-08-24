import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "FRIDAY AI Assistant"
    VERSION: str = "0.1.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "ollama") # ollama, openai, mock
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
