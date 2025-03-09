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

    def failure(self, cb, exc):
        logger.warning(f"❌ Fallo #{cb.current_failures} en {self.service_name}: {exc}")
        if cb.current_failures < 3:  # 3 = fail_max
            logger.info(f"⚠️ {3 - cb.current_failures} fallos más antes de abrir el Circuit Breaker")

    def success(self, cb):
        if cb.current_failures > 0:
            logger.info(f"✅ Solicitud exitosa a {self.service_name} después de {cb.current_failures} fallos")
        cb._failures = 0
        cb.current_failures = 0
            

# Crear el circuit breaker para Aldeamo
aldeamo_breaker = pybreaker.CircuitBreaker(
    fail_max=3,  # 3 fallos consecutivos para abrir el circuito
    reset_timeout=15,  # 15 segundos para pasar de open a half-open (tiempo razonable para pruebas)
    exclude=[],  # No excluir ninguna excepción
    name="aldeamo_service",
    listeners=[CircuitBreakerListener("Aldeamo")]
)