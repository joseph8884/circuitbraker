import logging
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Servicio de Notificaciones Aldeamo")

class NotificationRequest(BaseModel):
    message: str
    customer_id: str

class NotificationResponse(BaseModel):
    provider: str
    status: str
    message_id: str

@app.get("/")
async def read_root():
    return {"message": "Servicio de Notificaciones Aldeamo", "status": "online"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/notify", response_model=NotificationResponse)
async def send_notification(notification: NotificationRequest):
    # Simular fallas aleatorias basadas en el FAILURE_RATE configurado
    if random.random() < settings.FAILURE_RATE:
        logger.error(f"Simulando falla en el servicio Aldeamo")
        raise HTTPException(status_code=500, detail="Error al enviar notificación con Aldeamo")
    
    # Procesar la notificación (simulado)
    logger.info(f"Enviando notificación a través de Aldeamo para el cliente {notification.customer_id}")
    logger.info(f"Mensaje: {notification.message}")
    
    # Simular un pequeño retardo para enviar la notificación
    import asyncio
    await asyncio.sleep(0.2)
    
    return {
        "provider": "Aldeamo",
        "status": "delivered",
        "message_id": f"aldeamo_{random.randint(1000, 9999)}_{notification.customer_id}"
    }

@app.post("/toggle-failure")
async def toggle_failure(failure_rate: float):
    """Endpoint para cambiar la tasa de fallos (para pruebas)"""
    old_rate = settings.FAILURE_RATE
    settings.FAILURE_RATE = max(0.0, min(1.0, failure_rate))  # Asegurar que esté entre 0 y 1
    logger.info(f"Tasa de fallos de Aldeamo cambiada de {old_rate} a {settings.FAILURE_RATE}")
    return {"status": "updated", "failure_rate": settings.FAILURE_RATE}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True)