"""
Dispara webhooks a n8n para automatizar el envío de recetas.
El PDF viaja como base64 en el payload — n8n lo decodifica y adjunta.
"""
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("sistema-medico")

async def notificar_receta_lista(
    paciente_nombre: str,
    paciente_telefono: str,
    paciente_email: str,
    receta_id: str,
    pdf_b64: str,
    doctor_nombre: str,
    consultorio_nombre: str,
):
    """
    Payload que recibe n8n:
    {
      "evento": "receta_lista",
      "receta_id": "...",
      "pdf_base64": "...",          ← PDF codificado, n8n lo adjunta
      "paciente": { nombre, telefono, email },
      "doctor": "Dr. Nombre Apellido",
      "consultorio": "Nombre consultorio"
    }
    n8n decodifica el base64, crea el archivo y lo envía por WhatsApp/email.
    """
    if not settings.N8N_WEBHOOK_URL:
        logger.warning("N8N_WEBHOOK_URL no configurado — envío omitido")
        return

    payload = {
        "evento": "receta_lista",
        "receta_id": receta_id,
        "pdf_base64": pdf_b64,
        "paciente": {
            "nombre": paciente_nombre,
            "telefono": paciente_telefono,
            "email": paciente_email,
        },
        "doctor": doctor_nombre,
        "consultorio": consultorio_nombre,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                settings.N8N_WEBHOOK_URL,
                json=payload,
                headers={"X-Webhook-Secret": settings.N8N_WEBHOOK_SECRET},
            )
            resp.raise_for_status()
            logger.info(f"Webhook n8n disparado OK para receta {receta_id}")
    except httpx.TimeoutException:
        logger.error(f"Timeout al llamar webhook n8n para receta {receta_id}")
    except Exception as e:
        logger.error(f"Error en webhook n8n: {e}")
