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
from pydantic import BaseModel
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


# ── ENDPOINT PÚBLICO: listar doctores de un consultorio ──────
@router.get("/publico/{slug}/doctores")
def doctores_publicos(slug: str, db: Session = Depends(get_db)):
    """Lista los doctores activos de un consultorio por su slug. Público."""
    consultorio = db.query(Consultorio).filter(Consultorio.slug == slug).first()
    if not consultorio:
        raise HTTPException(status_code=404, detail="Consultorio no encontrado")
    doctores = db.query(Doctor).filter(
        Doctor.consultorio_id == consultorio.id,
        Doctor.activo == True,
    ).order_by(Doctor.nombre).all()
    return [
        {
            "id": str(d.id),
            "nombre": d.nombre,
            "apellido": d.apellido,
            "especialidad": d.especialidad,
        }
        for d in doctores
    ]


# ── ENDPOINT PÚBLICO: solicitud de cita ─────────────────────
class SolicitudCitaPublica(BaseModel):
    consultorio_slug: str
    nombre: str
    apellido: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_solicitada: str          # llega como string del datetime-local
    motivo: str
    doctor_id: Optional[uuid.UUID] = None


@router.post("/publico/solicitar-cita", status_code=201)
def solicitar_cita_publica(
    data: SolicitudCitaPublica,
    db: Session = Depends(get_db),
):
    """
    Crea una solicitud de cita desde el portal público (sin autenticación).
    - Si el paciente ya existe (match por email o teléfono), se respeta su
      doctor de cabecera.
    - Si es nuevo, el doctor elegido queda como su doctor de cabecera.
    """
    # Resolver el consultorio por slug
    consultorio = db.query(Consultorio).filter(
        Consultorio.slug == data.consultorio_slug
    ).first()
    if not consultorio:
        raise HTTPException(status_code=404, detail="Consultorio no encontrado")

    # Buscar paciente existente por email o teléfono dentro del consultorio
    paciente = None
    if data.email:
        paciente = db.query(Paciente).filter(
            Paciente.consultorio_id == consultorio.id,
            Paciente.email == data.email,
        ).first()
    if not paciente and data.telefono:
        paciente = db.query(Paciente).filter(
            Paciente.consultorio_id == consultorio.id,
            Paciente.telefono == data.telefono,
        ).first()

    if paciente:
        # Paciente EXISTENTE → se respeta su doctor de cabecera
        doctor_asignado = paciente.doctor_cabecera_id
    else:
        # Paciente NUEVO → el doctor elegido queda como su cabecera
        doctor_asignado = data.doctor_id
        paciente = Paciente(
            consultorio_id=consultorio.id,
            nombre=data.nombre,
            apellido=data.apellido,
            email=data.email,
            telefono=data.telefono,
            doctor_cabecera_id=data.doctor_id,
        )
        db.add(paciente)
        db.flush()  # obtiene paciente.id sin cerrar la transacción

    # Parsear la fecha (string local, sin conversión UTC)
    try:
        fecha = datetime.strptime(
            data.fecha_solicitada.replace('T', ' ')[:16], '%Y-%m-%d %H:%M'
        )
    except ValueError:
        fecha = datetime.utcnow()

    cita = Cita(
        consultorio_id=consultorio.id,
        paciente_id=paciente.id,
        doctor_id=doctor_asignado,   # puede ser None si nadie fue elegido
        fecha_solicitada=fecha,
        motivo=data.motivo,
        estado="pendiente",
    )
    db.add(cita)
    db.commit()
    db.refresh(cita)

    return {
        "mensaje": "Solicitud de cita recibida",
        "cita_id": str(cita.id),
        "paciente": f"{paciente.nombre} {paciente.apellido}",
    }