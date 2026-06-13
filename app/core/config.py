from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Sistema Medico"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "1869f31777826dd1ac06dc4e7830bcf66c849b3a9c7b61de12f8d7b9edfba58b"
    DATABASE_URL: str = "postgresql://user:pass@localhost/medico"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    N8N_WEBHOOK_URL: str = ""
    N8N_WEBHOOK_SECRET: str = ""
    ENCRYPTION_KEY: str = "ewIeuzOatrxsmU0DDO02994NQxbOie1RsLKTeY6CBB0"  # ← Nuevo: clave Fernet para cifrado
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
