"""
Rate Limiting — Sistema Médico
Limita las peticiones por IP para prevenir ataques de fuerza bruta.
- Login: máximo 5 intentos por minuto por IP
- API general: máximo 100 peticiones por minuto por IP
"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException, status

# Almacén en memoria: {ip: [timestamps]}
_intentos: dict = defaultdict(list)

def _limpiar_viejos(ip: str, ventana_segundos: int):
    ahora = time.time()
    _intentos[ip] = [t for t in _intentos[ip] if ahora - t < ventana_segundos]

def verificar_rate_limit(
    request: Request,
    max_intentos: int = 100,
    ventana_segundos: int = 60,
    mensaje: str = "Demasiadas peticiones. Intenta en un momento.",
):
    """
    Verifica que la IP no haya excedido el límite de peticiones.
    Llama esto al inicio de endpoints sensibles.
    """
    ip = request.client.host if request.client else "unknown"
    _limpiar_viejos(ip, ventana_segundos)

    if len(_intentos[ip]) >= max_intentos:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=mensaje,
            headers={"Retry-After": str(ventana_segundos)},
        )
    _intentos[ip].append(time.time())


# Decoradores de conveniencia
def rate_limit_login(request: Request):
    """5 intentos de login por minuto por IP."""
    verificar_rate_limit(
        request,
        max_intentos=5,
        ventana_segundos=60,
        mensaje="Demasiados intentos de login. Espera 1 minuto.",
    )

def rate_limit_api(request: Request):
    """100 peticiones por minuto por IP."""
    verificar_rate_limit(request, max_intentos=100, ventana_segundos=60)
