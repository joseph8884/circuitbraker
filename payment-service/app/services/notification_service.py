import httpx
import logging
import pybreaker
import asyncio
import time
import random
from ..config import settings
from ..circuit_breaker import aldeamo_breaker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.aldeamo_url = "http://aldeamo-service:8001/notify"
        self.twilio_url = "http://twilio-service:8002/notify"
        self.current_service = "Aldeamo"  # Servicio predeterminado
        self.recovery_check_interval = 5  # Verificar cada 5 segundos si Aldeamo se recuperó
        self.last_check_time = 0

    @aldeamo_breaker
    async def notify_with_aldeamo(self, message: str, customer_id: str):
        """Enviar notificación utilizando Aldeamo con Circuit Breaker"""
        logger.info(f"Intentando notificar con Aldeamo: {message}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                self.aldeamo_url,
                json={"message": message, "customer_id": customer_id}
            )

            if response.status_code != 200:
                logger.error(f"Error en respuesta de Aldeamo: {response.status_code}")
                raise Exception(f"Error en Aldeamo: {response.text}")

            logger.info("✅ Notificación enviada con éxito a través de Aldeamo")
            self.current_service = "Aldeamo"
            return response.json()

    async def notify_with_twilio(self, message: str, customer_id: str):
        """Enviar notificación utilizando Twilio como respaldo"""
        logger.info(f"Intentando notificar con Twilio: {message}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                self.twilio_url,
                json={"message": message, "customer_id": customer_id}
            )

            if response.status_code != 200:
                raise Exception(f"Error en Twilio: {response.text}")

            logger.info("✅ Notificación enviada con éxito a través de Twilio")
            self.current_service = "Twilio"
            return response.json()

    async def check_aldeamo_health(self):
        """Verificar si Aldeamo está funcionando"""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get("http://aldeamo-service:8001/health")
                return response.status_code == 200
        except Exception:
            return False

    async def send_notification(self, message: str, customer_id: str):
        """
        Intenta enviar notificación a través de Aldeamo,
        si falla o el circuito está abierto, utiliza Twilio como respaldo
        """
        current_time = time.time()
        circuit_state = aldeamo_breaker.current_state

        # Si el circuito está en estado 'half-open', vamos a intentar con Aldeamo
        # para ver si se ha recuperado
        if circuit_state == 'half-open':
            logger.info("🔄 Circuito en estado semi-abierto, probando si Aldeamo se ha recuperado...")

        try:
            # Intentar con Aldeamo (protegido por el Circuit Breaker)
            # Si el circuito está cerrado o semi-abierto, intentará con Aldeamo
            # Si está abierto, lanzará CircuitBreakerError
            result = await self.notify_with_aldeamo(message, customer_id)
            
            # Si llegamos aquí, la notificación con Aldeamo fue exitosa
            if circuit_state == 'half-open':
                logger.info("✅ Aldeamo se ha recuperado! Circuito cerrado nuevamente.")
            
            return result
            
        except pybreaker.CircuitBreakerError:
            # Circuit Breaker está abierto, usar Twilio como respaldo
            logger.warning("🔄 Circuit Breaker abierto para Aldeamo, usando Twilio como respaldo")
            return await self.notify_with_twilio(message, customer_id)
            
        except Exception as e:
            # Error al intentar con Aldeamo, pero el circuito aún no está abierto
            # Esto incrementa el contador de fallos en el CircuitBreaker
            logger.error(f"❌ Error al notificar con Aldeamo: {str(e)}")
            
            # Intentar con Twilio como fallback
            return await self.notify_with_twilio(message, customer_id)

    async def try_aldeamo_directly(self, message: str, customer_id: str):
        """Intenta enviar una notificación directamente a Aldeamo, sin pasar por el circuit breaker"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.aldeamo_url,
                    json={"message": message, "customer_id": customer_id}
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_current_service(self):
        """Obtener el servicio de notificación actual"""
        return self.current_service

    def get_circuit_state(self):
        """Obtener el estado actual del Circuit Breaker"""
        state = str(aldeamo_breaker.current_state)
        state_map = {
            'closed': 'CERRADO (usando Aldeamo)',
            'open': 'ABIERTO (usando Twilio)',
            'half-open': 'SEMI-ABIERTO (probando Aldeamo)'
        }

        return {
            "state": state,
            "description": state_map.get(state, state),
            "failures": aldeamo_breaker.current_failures,
            "threshold": 3,  # Matches the setting in circuit_breaker.py
            "current_service": self.current_service,
            "reset_timeout": 15  # Matches the reset_timeout in circuit_breaker.py
        }


# Instancia global del servicio de notificación
notification_service = NotificationService()