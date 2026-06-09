from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
import uuid

from app.db.session import get_db
from app.core.dependencies import get_current_doctor, require_admin
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("/")
def listar_audit_log(
    limit: int = 50,
    accion: Optional[str] = None,
    recurso: Optional[str] = None,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """Lista el historial de acciones del consultorio."""
    q = db.query(AuditLog).filter(
        AuditLog.consultorio_id == doctor.consultorio_id
    )
    if accion:
        q = q.filter(AuditLog.accion == accion)
    if recurso:
        q = q.filter(AuditLog.recurso == recurso)

    logs = q.order_by(desc(AuditLog.created_at)).limit(limit).all()

    return [
        {
            "id": str(log.id),
            "doctor_email": log.doctor_email,
            "accion": log.accion,
            "recurso": log.recurso,
            "recurso_id": str(log.recurso_id) if log.recurso_id else None,
            "detalle": log.detalle,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/resumen")
def resumen_auditoria(
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """Conteo de acciones por tipo para el dashboard."""
    from sqlalchemy import func
    resultados = (
        db.query(AuditLog.accion, func.count(AuditLog.id).label("total"))
        .filter(AuditLog.consultorio_id == doctor.consultorio_id)
        .group_by(AuditLog.accion)
        .all()
    )
    return {r.accion: r.total for r in resultados}
