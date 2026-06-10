"""
Endpoint de agenda/calendario.
- Doctor normal: ve solo sus propias citas.
- Admin: puede ver todas, o filtrar por un doctor específico.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import uuid
from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.cita import Cita
from app.models.paciente import Paciente

router = APIRouter(prefix="/agenda", tags=["Agenda"])


@router.get("/")
def obtener_agenda(
    anio: int,
    mes: int,
    doctor_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """
    Devuelve las citas del mes indicado para el calendario.
    - Si el usuario es admin y pasa doctor_id, filtra por ese doctor.
    - Si el usuario es admin sin doctor_id, devuelve todas.
    - Si es doctor normal, siempre devuelve solo las suyas.
    """
    q = db.query(Cita).filter(Cita.consultorio_id == doctor.consultorio_id)

    es_admin = getattr(doctor, "rol", "doctor") == "admin"
    if es_admin:
        if doctor_id:
            q = q.filter(Cita.doctor_id == doctor_id)
    else:
        q = q.filter(Cita.doctor_id == doctor.id)

    # Filtrar por mes
    inicio = datetime(anio, mes, 1)
    if mes == 12:
        fin = datetime(anio + 1, 1, 1)
    else:
        fin = datetime(anio, mes + 1, 1)
    q = q.filter(Cita.fecha_solicitada >= inicio, Cita.fecha_solicitada < fin)

    citas = q.order_by(Cita.fecha_solicitada).all()

    # Cachear nombres de pacientes
    pids = list({c.paciente_id for c in citas})
    pacientes = {}
    if pids:
        for p in db.query(Paciente).filter(Paciente.id.in_(pids)).all():
            pacientes[p.id] = f"{p.nombre} {p.apellido}"

    return [
        {
            "id": str(c.id),
            "fecha": c.fecha_solicitada.isoformat(),
            "motivo": c.motivo,
            "estado": c.estado,
            "paciente": pacientes.get(c.paciente_id, "Paciente"),
            "doctor_id": str(c.doctor_id) if c.doctor_id else None,
        }
        for c in citas
    ]
