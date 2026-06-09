"""
Endpoints del dashboard del médico:
- Resumen de citas del día
- Estadísticas rápidas
- Endpoint público para solicitud de citas (sin autenticación)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.cita import Cita
from app.models.paciente import Paciente
from app.models.doctor import Doctor
from app.models.consultorio import Consultorio

router = APIRouter(tags=["Dashboard"])


# ── DASHBOARD PRIVADO ────────────────────────────────────────
@router.get("/dashboard/resumen")
def resumen_dashboard(
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """Estadísticas rápidas para la pantalla principal del doctor."""
    hoy = date.today()
    cid = doctor.consultorio_id

    citas_hoy = db.query(Cita).filter(
        Cita.consultorio_id == cid,
        func.date(Cita.fecha_solicitada) == hoy,
    ).count()

    pendientes = db.query(Cita).filter(
        Cita.consultorio_id == cid,
        Cita.estado == "pendiente",
    ).count()

    total_pacientes = db.query(Paciente).filter(
        Paciente.consultorio_id == cid,
        Paciente.activo == True,
    ).count()

    proximas = db.query(Cita).filter(
        Cita.consultorio_id == cid,
        Cita.fecha_solicitada >= datetime.now(),
        Cita.estado.in_(["pendiente", "confirmada"]),
    ).order_by(Cita.fecha_solicitada).limit(5).all()

    return {
        "citas_hoy": citas_hoy,
        "pendientes": pendientes,
        "total_pacientes": total_pacientes,
        "proximas_citas": [
            {
                "id": str(c.id),
                "paciente_id": str(c.paciente_id),
                "fecha": c.fecha_solicitada.isoformat(),
                "motivo": c.motivo,
                "estado": c.estado,
            }
            for c in proximas
        ],
    }


@router.get("/dashboard/me")
def get_me(doctor=Depends(get_current_doctor)):
    """Datos del doctor autenticado."""
    return {
        "id": str(doctor.id),
        "nombre": doctor.nombre,
        "apellido": doctor.apellido,
        "email": doctor.email,
        "especialidad": doctor.especialidad,
        "cedula_profesional": doctor.cedula_profesional,
        "rol": doctor.rol,
        "consultorio_id": str(doctor.consultorio_id),
    }


# ── ENDPOINT PÚBLICO: solicitud de cita ─────────────────────
class SolicitudCitaPublica(BaseModel):
    consultorio_slug: str
    nombre: str
    apellido: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_solicitada: datetime
    motivo: str

@router.post("/publico/solicitar-cita", status_code=201)
def solicitar_cita_publica(data: SolicitudCitaPublica, db: Session = Depends(get_db)):
    """
    Endpoint público — no requiere autenticación.
    El paciente llena un formulario y queda registrado con estado 'pendiente'.
    """
    consultorio = db.query(Consultorio).filter(
        Consultorio.slug == data.consultorio_slug,
        Consultorio.activo == True,
    ).first()
    if not consultorio:
        raise HTTPException(status_code=404, detail="Consultorio no encontrado")

    # Buscar o crear paciente por email/teléfono
    paciente = None
    if data.email:
        paciente = db.query(Paciente).filter(
            Paciente.consultorio_id == consultorio.id,
            Paciente.email == data.email,
        ).first()

    if not paciente:
        paciente = Paciente(
            consultorio_id=consultorio.id,
            nombre=data.nombre,
            apellido=data.apellido,
            email=data.email,
            telefono=data.telefono,
        )
        db.add(paciente)
        db.flush()

    cita = Cita(
        consultorio_id=consultorio.id,
        paciente_id=paciente.id,
        fecha_solicitada=data.fecha_solicitada,
        motivo=data.motivo,
        estado="pendiente",
    )
    db.add(cita)
    db.commit()

    return {
        "mensaje": "Cita solicitada correctamente",
        "cita_id": str(cita.id),
        "estado": "pendiente",
    }
