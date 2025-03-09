import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Configuración para simular fallas
    FAILURE_RATE: float = float(os.getenv("TWILIO_FAILURE_RATE", "0.0"))  # Porcentaje de fallas (0.0 - 1.0)

    class Config:
        env_file = ".env"


settings = Settings()