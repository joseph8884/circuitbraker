import pybreaker
import logging
import time
from threading import Timer
from .config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuración del Circuit Breaker para el servicio Aldeamo
class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def __init__(self, service_name):
        self.service_name = service_name

    def state_change(self, cb, old_state, new_state):
        state_map = {
            'closed': 'CERRADO (usando Aldeamo)',
            'open': 'ABIERTO (usando Twilio)',
            'half-open': 'SEMI-ABIERTO (probando Aldeamo)'
        }
        old_state_desc = state_map.get(str(old_state), str(old_state))
        new_state_desc = state_map.get(str(new_state), str(new_state))

        logger.info(f"🔄 Circuit Breaker para {self.service_name} cambió de {old_state_desc} a {new_state_desc}")

        # Si el circuito se abre, programar una verificación para el modo half-open
        if str(new_state) == 'open':
            logger.warning(
                f"⚠️ Circuit Breaker abierto: Se usará Twilio como respaldo por los próximos {settings.RESET_TIMEOUT} segundos")

    def failure(self, cb, exc):
        logger.warning(f"❌ Fallo #{cb.current_failures} en {self.service_name}: {exc}")
        remaining = settings.FAILURE_THRESHOLD - cb.current_failures
        if remaining > 0:
            logger.info(f"⚠️ {remaining} fallos más antes de abrir el Circuit Breaker")

    def success(self, cb):
        if cb.current_failures > 0:
            logger.info(f"✅ Solicitud exitosa a {self.service_name} después de {cb.current_failures} fallos")
            # Resetear el contador de fallos cuando hay un éxito
            cb._failures = 0
            cb.current_failures = 0
        else:
            logger.info(f"✅ Solicitud exitosa a {self.service_name}")


# Asegurar valores de configuración razonables para pruebas con Postman
reset_timeout = 15  # 15 segundos es un tiempo razonable para pruebas

# Crear el circuit breaker para Aldeamo
aldeamo_breaker = pybreaker.CircuitBreaker(
    fail_max=3,  # Solo 3 fallos consecutivos para abrir el circuito (más rápido para pruebas)
    reset_timeout=reset_timeout,  # Tiempo en segundos para pasar de open a half-open
    exclude=[],  # No excluir ninguna excepción
    name="aldeamo_service",
    listeners=[CircuitBreakerListener("Aldeamo")]
)