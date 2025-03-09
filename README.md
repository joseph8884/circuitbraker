# Microservicios de Pagos y Notificaciones

Este proyecto implementa un sistema de microservicios con FastAPI para procesar pagos y enviar notificaciones con tolerancia a fallos mediante el patrón Circuit Breaker.

## Descripción

El sistema consta de tres microservicios:

1. **Servicio de Pagos**: Recibe solicitudes de pago y coordina las notificaciones
2. **Servicio de Notificaciones Aldeamo**: Servicio principal de notificaciones
3. **Servicio de Notificaciones Twilio**: Servicio de respaldo para notificaciones

El servicio de pagos utiliza el patrón Circuit Breaker (implementado con `pybreaker`) para manejar fallos en el servicio de notificaciones principal (Aldeamo) y cambiar automáticamente al servicio de respaldo (Twilio) cuando sea necesario.

## Requisitos

- Python 3.8+
- Docker y Docker Compose

## Instalación y Ejecución

1. Clonar el repositorio:
```
git clone https://github.com/usuario/payment-notification-microservices.git
cd payment-notification-microservices
```

2. Iniciar los servicios con Docker Compose:
```
docker-compose up -d
```

3. Servicios disponibles:
   - Servicio de Pagos: http://localhost:8000
   - Servicio Aldeamo: http://localhost:8001
   - Servicio Twilio: http://localhost:8002

## Uso

Para procesar un pago y enviar una notificación:

```bash
curl -X POST http://localhost:8000/payments \
  -H "Content-Type: application/json" \
  -d '{"amount": 100.0, "customer_id": "123", "message": "Pago recibido"}'
```

## Arquitectura

El sistema utiliza el patrón Circuit Breaker para proporcionar tolerancia a fallos:

1. El servicio de pagos intenta enviar notificaciones a través del servicio Aldeamo.
2. Si el servicio Aldeamo falla, el circuit breaker se abre y las notificaciones se envían a través de Twilio.
3. El circuit breaker intenta restablecer periódicamente la conexión con Aldeamo.
4. El servicio de pagos registra qué proveedor de notificaciones está utilizando.

## Configuración

Los parámetros del circuit breaker se pueden configurar en `payment-service/app/circuit_breaker.py`.