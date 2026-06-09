"""
Servicio de auditoría — registra todas las acciones del sistema.
Se llama desde los endpoints después de cada operación importante.
"""
import json
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

# Acciones disponibles
class Accion:
    LOGIN        = "LOGIN"
    LOGOUT       = "LOGOUT"
    VER          = "VER"
    CREAR        = "CREAR"
    EDITAR       = "EDITAR"
    ELIMINAR     = "ELIMINAR"
    ENVIAR       = "ENVIAR"
    GENERAR_PDF  = "GENERAR_PDF"

# Recursos disponibles
class Recurso:
    PACIENTE   = "paciente"
    CITA       = "cita"
    RECETA     = "receta"
    DOCTOR     = "doctor"
    SISTEMA    = "sistema"


def registrar(
    db: Session,
    accion: str,
    recurso: str,
    doctor_id: str = None,
    consultorio_id: str = None,
    doctor_email: str = None,
    recurso_id: str = None,
    detalle: dict = None,
    ip_address: str = None,
    user_agent: str = None,
) -> None:
    """
    Registra una acción en el audit_log.
    Es fire-and-forget — si falla no interrumpe la operación principal.
    """
    try:
        log = AuditLog(
            doctor_id=UUID(doctor_id) if doctor_id else None,
            consultorio_id=UUID(consultorio_id) if consultorio_id else None,
            doctor_email=doctor_email,
            accion=accion,
            recurso=recurso,
            recurso_id=UUID(recurso_id) if recurso_id else None,
            detalle=json.dumps(detalle, ensure_ascii=False) if detalle else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()
    except Exception as e:
        import logging
        logging.getLogger("sistema-medico").error(f"Error en auditoría: {e}")


def registrar_desde_request(
    db: Session,
    request,
    doctor,
    accion: str,
    recurso: str,
    recurso_id: str = None,
    detalle: dict = None,
) -> None:
    """Helper que extrae IP y User-Agent del request automáticamente."""
    registrar(
        db=db,
        accion=accion,
        recurso=recurso,
        doctor_id=str(doctor.id),
        consultorio_id=str(doctor.consultorio_id),
        doctor_email=doctor.email,
        recurso_id=recurso_id,
        detalle=detalle,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
