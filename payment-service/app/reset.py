"""
Módulo para reiniciar el estado del circuit breaker.
"""
import logging
from .circuit_breaker import aldeamo_breaker
from pybreaker import CircuitClosedState

logger = logging.getLogger(__name__)


def force_circuit_closed():
    """
    Fuerza el reinicio del circuit breaker para Aldeamo, cambiando su estado a cerrado.
    """
    try:
        logger.info("🔄 Forzando reinicio del Circuit Breaker a estado CERRADO")

        # Reiniciar los contadores internos
        aldeamo_breaker._last_failure = None
        aldeamo_breaker._failures = 0
        aldeamo_breaker.current_failures = 0

        # Forzar cambio de estado a cerrado
        if aldeamo_breaker._state and not isinstance(aldeamo_breaker._state, CircuitClosedState):
            aldeamo_breaker._state = CircuitClosedState(aldeamo_breaker)
            logger.info("✅ Circuit Breaker forzado a estado CERRADO exitosamente")

        return True
    except Exception as e:
        logger.error(f"❌ Error al forzar reinicio del Circuit Breaker: {str(e)}")
        return False