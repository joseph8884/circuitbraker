import logging
import random
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.openapi.utils import get_openapi
from .config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Servicio de Notificaciones Twilio",
    description="API para enviar notificaciones usando el proveedor Twilio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


class NotificationRequest(BaseModel):
    message: str = Field(..., description="Mensaje que será enviado al cliente",
                         example="Tu pago ha sido procesado con éxito")
    customer_id: str = Field(..., description="ID único del cliente", example="cust_12345")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Tu pago ha sido procesado con éxito",
                "customer_id": "cust_12345"
            }
        }
    }


class NotificationResponse(BaseModel):
    provider: str = Field(..., description="Proveedor que entregó el mensaje", example="Twilio")
    status: str = Field(..., description="Estado de entrega del mensaje", example="delivered")
    message_id: str = Field(..., description="ID único del mensaje enviado", example="twilio_5678_cust_12345")

    model_config = {
        "json_schema_extra": {
            "example": {
                "provider": "Twilio",
                "status": "delivered",
                "message_id": "twilio_5678_cust_12345"
            }
        }
    }


@app.get("/",
         summary="Información del servicio",
         description="Obtiene información básica sobre el servicio de notificaciones Twilio",
         tags=["Información"])
async def read_root():
    """
    Devuelve información básica sobre el estado del servicio Twilio.
    """
    return {"message": "Servicio de Notificaciones Twilio", "status": "online"}


@app.get("/health",
         summary="Verificación de salud",
         description="Verifica el estado de salud del servicio",
         tags=["Información"])
async def health_check():
    """
    Endpoint para verificar si el servicio está funcionando correctamente.
    Útil para healthchecks y monitoreo.
    """
    return {"status": "healthy"}


@app.post("/notify",
          response_model=NotificationResponse,
          summary="Enviar notificación",
          description="Envía una notificación a un cliente a través del servicio Twilio",
          tags=["Notificaciones"],
          responses={
              200: {"description": "Notificación enviada con éxito"},
              500: {"description": "Error al enviar la notificación"}
          })
async def send_notification(notification: NotificationRequest):
    # Simular fallas aleatorias basadas en el FAILURE_RATE configurado
    if random.random() < settings.FAILURE_RATE:
        logger.error(f"Simulando falla en el servicio Twilio")
        raise HTTPException(status_code=500, detail="Error al enviar notificación con Twilio")

    # Procesar la notificación (simulado)
    logger.info(f"Enviando notificación a través de Twilio para el cliente {notification.customer_id}")
    logger.info(f"Mensaje: {notification.message}")

    # Simular un pequeño retardo para enviar la notificación
    import asyncio
    await asyncio.sleep(0.1)

    return {
        "provider": "Twilio",
        "status": "delivered",
        "message_id": f"twilio_{random.randint(1000, 9999)}_{notification.customer_id}"
    }


@app.post("/toggle-failure",
          summary="Modificar tasa de fallos",
          description="Cambia la tasa de fallos del servicio para pruebas",
          tags=["Configuración"],
          responses={
              200: {"description": "Tasa de fallos actualizada correctamente"}
          })
async def toggle_failure(failure_rate: float = Query(
    ...,
    description="Tasa de fallos entre 0.0 (sin fallos) y 1.0 (siempre falla)",
    ge=0.0,
    le=1.0)):
    """Endpoint para cambiar la tasa de fallos (para pruebas)"""
    old_rate = settings.FAILURE_RATE
    settings.FAILURE_RATE = max(0.0, min(1.0, failure_rate))  # Asegurar que esté entre 0 y 1
    logger.info(f"Tasa de fallos de Twilio cambiada de {old_rate} a {settings.FAILURE_RATE}")
    return {"status": "updated", "failure_rate": settings.FAILURE_RATE}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="API de Servicio de Notificaciones Twilio",
        version="1.0.0",
        description="""
        # API de Servicio de Notificaciones Twilio

        Esta API permite enviar notificaciones a clientes a través del proveedor Twilio.
        Funciona como servicio de respaldo cuando el servicio principal (Aldeamo) no está disponible.
        """,
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)