"""
Servicio de cifrado — Sistema Médico
=====================================
Cifra y descifra campos sensibles usando Fernet (AES-128-CBC + HMAC-SHA256).
La clave se guarda en .env como ENCRYPTION_KEY.

Generar una clave nueva:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
import logging
from typing import Optional
from functools import lru_cache

logger = logging.getLogger("sistema-medico")

# Prefijo para identificar campos cifrados en BD
CIFRADO_PREFIX = "ENC:"


@lru_cache(maxsize=1)
def _get_fernet():
    """Carga y cachea la instancia Fernet con la clave del .env."""
    from cryptography.fernet import Fernet
    from app.core.config import settings

    key = getattr(settings, "ENCRYPTION_KEY", None)
    if not key:
        raise ValueError("ENCRYPTION_KEY no está configurada en .env")
    return Fernet(key.encode() if isinstance(key, str) else key)


def cifrar(texto: Optional[str]) -> Optional[str]:
    """
    Cifra un texto plano y retorna el texto cifrado con prefijo ENC:.
    Si el texto es None o vacío, lo retorna tal cual.
    Si ya está cifrado, no lo vuelve a cifrar.
    """
    if not texto:
        return texto
    if texto.startswith(CIFRADO_PREFIX):
        return texto  # Ya está cifrado
    try:
        f = _get_fernet()
        cifrado = f.encrypt(texto.encode("utf-8")).decode("utf-8")
        return f"{CIFRADO_PREFIX}{cifrado}"
    except Exception as e:
        logger.error(f"Error al cifrar: {e}")
        return texto  # Retorna sin cifrar antes de perder el dato


def descifrar(texto: Optional[str]) -> Optional[str]:
    """
    Descifra un texto con prefijo ENC:.
    Si no tiene el prefijo (dato legacy sin cifrar), lo retorna tal cual.
    Si es None o vacío, lo retorna tal cual.
    """
    if not texto:
        return texto
    if not texto.startswith(CIFRADO_PREFIX):
        return texto  # Dato legacy sin cifrar — compatible hacia atrás
    try:
        f = _get_fernet()
        contenido = texto[len(CIFRADO_PREFIX):]
        return f.decrypt(contenido.encode("utf-8")).decode("utf-8")
    except Exception as e:
        logger.error(f"Error al descifrar: {e}")
        return "[Error al descifrar]"


def esta_cifrado(texto: Optional[str]) -> bool:
    """Verifica si un campo está cifrado."""
    return bool(texto and texto.startswith(CIFRADO_PREFIX))
