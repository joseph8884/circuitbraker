from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from .services.notification_service import notification_service
from fastapi.openapi.utils import get_openapi
from .reset import force_circuit_closed

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Servicio de Pagos",
    description="API para procesar pagos y enviar notificaciones usando el patrón Circuit Breaker",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


class PaymentRequest(BaseModel):
    amount: float
    customer_id: str
    message: str = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "amount": 100.50,
                "customer_id": "cust_12345",
                "message": "Gracias por tu pago"
            }
        }
    }


class PaymentResponse(BaseModel):
    payment_id: str
    status: str
    notification_service: str
    notification_status: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "payment_id": "pmt_12345",
                "status": "completed",
                "notification_service": "Aldeamo",
                "notification_status": "sent"
            }
        }
    }


@app.get("/")
async def read_root():
    return {"message": "Servicio de Pagos", "status": "online"}


@app.get("/health",
         summary="Estado del servicio",
         description="Verifica el estado de salud del servicio y muestra el estado del circuit breaker",
         tags=["Información"])
async def health_check():
    circuit_state = notification_service.get_circuit_state()
    return {
        "status": "healthy",
        "current_notification_service": notification_service.get_current_service(),
        "circuit_breaker": circuit_state
    }


@app.post("/payments", response_model=PaymentResponse)
async def process_payment(payment: PaymentRequest):
    try:
        # Simular procesamiento de pago
        logger.info(f"Procesando pago de {payment.amount} para el cliente {payment.customer_id}")

        # Preparar mensaje de notificación
        message = payment.message or f"Se ha procesado un pago de ${payment.amount} con éxito."

        # Enviar notificación utilizando el servicio apropiado con circuit breaker
        notification_result = await notification_service.send_notification(
            message,
            payment.customer_id
        )

        # Obtener qué servicio de notificación se utilizó
        current_service = notification_service.get_current_service()
        logger.info(f"Pago procesado y notificado a través de {current_service}")

        return {
            "payment_id": "pmt_" + payment.customer_id,
            "status": "completed",
            "notification_service": current_service,
            "notification_status": "sent"
        }

    except Exception as e:
        logger.error(f"Error al procesar el pago: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al procesar el pago: {str(e)}")


@app.post("/force-recovery",
          summary="Forzar recuperación",
          description="Fuerza un intento de usar Aldeamo independientemente del estado del circuito",
          tags=["Administración"])
async def force_recovery():
    """
    Fuerza un intento de verificar y recuperar la conexión con Aldeamo.
    Útil para administradores cuando saben que Aldeamo está funcionando nuevamente.
    """
    try:
        aldeamo_health = await notification_service.check_aldeamo_health()
        if aldeamo_health:
            return {"status": "success", "message": "Aldeamo está funcionando correctamente"}
        else:
            return {"status": "warning", "message": "Aldeamo sigue sin responder"}
    except Exception as e:
        return {"status": "error", "message": f"Error al verificar Aldeamo: {str(e)}"}


@app.post("/reset-circuit",
          summary="Reiniciar Circuit Breaker",
          description="Reinicia el estado del Circuit Breaker a cerrado (usar con precaución)",
          tags=["Administración"])
async def reset_circuit():
    """
    Reinicia manualmente el estado del Circuit Breaker.
    Usar con precaución, ya que puede generar más fallos si Aldeamo no está realmente recuperado.
    """
    try:
        # Verificar primero si Aldeamo está funcionando
        aldeamo_health = await notification_service.check_aldeamo_health()

        if aldeamo_health:
            # Forzar reinicio del Circuit Breaker
            notification_service.current_service = "Aldeamo"
            success = force_circuit_closed()

            if success:
                return {
                    "status": "success", 
                    "message": "Circuit Breaker reiniciado. Aldeamo establecido como servicio predeterminado."
                }
            else:
                return {
                    "status": "error",
                    "message": "No se pudo reiniciar el Circuit Breaker"
                }
        else:
            return {
                "status": "warning",
                "message": "No se puede restablecer Aldeamo porque sigue fallando. Arregle primero Aldeamo."
            }
    except Exception as e:
        return {"status": "error", "message": f"Error al reiniciar circuit breaker: {str(e)}"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="API de Servicio de Pagos",
        version="1.0.0",
        description="""
        # API de Servicio de Pagos

        Esta API permite procesar pagos y enviar notificaciones a través de diferentes proveedores.

        ## Características

        * Procesamiento de pagos
        * Envío de notificaciones utilizando el patrón Circuit Breaker
        * Alternancia automática entre servicios de notificación (Aldeamo y Twilio)

        ## Flujo de trabajo

        1. La API recibe una solicitud de pago con un monto, ID de cliente y mensaje opcional
        2. Procesa el pago 
        3. Envía una notificación a través de Aldeamo (servicio principal)
        4. Si Aldeamo falla, utiliza Twilio como servicio de respaldo
        5. Registra qué proveedor de notificaciones está utilizando
        """,
        routes=app.routes,
    )

    # Personalizar los esquemas
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)