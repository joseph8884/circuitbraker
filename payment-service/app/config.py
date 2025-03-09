import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ALDEAMO_SERVICE_URL: str = os.getenv("ALDEAMO_SERVICE_URL", "http://aldeamo-service:8001")
    TWILIO_SERVICE_URL: str = os.getenv("TWILIO_SERVICE_URL", "http://twilio-service:8002")

    # Configuración del Circuit Breaker
    FAILURE_THRESHOLD: int = int(os.getenv("FAILURE_THRESHOLD", "3"))  # Número de fallos antes de abrir el circuito
    RECOVERY_TIMEOUT: int = int(os.getenv("RECOVERY_TIMEOUT", "5"))    # Segundos entre verificaciones de recuperación
    RESET_TIMEOUT: int = int(os.getenv("RESET_TIMEOUT", "15"))         # Segundos que el circuito permanece abierto

    model_config = {
        "env_file": ".env"
    }


settings = Settings()