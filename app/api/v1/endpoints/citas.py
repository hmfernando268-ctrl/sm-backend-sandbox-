from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.cita import Cita
from app.schemas.cita import CitaCreate, CitaUpdate, CitaResponse
from app.services.audit_service import registrar_desde_request, Accion, Recurso

router = APIRouter(prefix="/citas", tags=["Citas"])

@router.get("/", response_model=List[CitaResponse])
def listar_citas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    q = db.query(Cita).filter(Cita.consultorio_id == doctor.consultorio_id)
    if estado:
        q = q.filter(Cita.estado == estado)
    return q.order_by(Cita.fecha_solicitada).all()

@router.post("/", response_model=CitaResponse, status_code=201)
def crear_cita(
    data: CitaCreate,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    cita = Cita(**data.model_dump(), consultorio_id=doctor.consultorio_id)
    db.add(cita)
    db.commit()
    db.refresh(cita)
    registrar_desde_request(
        db, request, doctor, Accion.CREAR, Recurso.CITA,
        recurso_id=str(cita.id),
        detalle={"paciente_id": str(data.paciente_id), "motivo": data.motivo[:50]},
    )
    return cita

@router.patch("/{cita_id}", response_model=CitaResponse)
def actualizar_cita(
    cita_id: uuid.UUID,
    data: CitaUpdate,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    cita = db.query(Cita).filter(
        Cita.id == cita_id,
        Cita.consultorio_id == doctor.consultorio_id,
    ).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    estado_anterior = cita.estado

    if data.estado is not None:
        cita.estado = data.estado
        # Autoasignación: si el doctor confirma y la cita no tiene doctor,
        # se asigna a sí mismo automáticamente
        if data.estado == "confirmada" and cita.doctor_id is None:
            cita.doctor_id = doctor.id

    if data.notas_doctor is not None:
        cita.notas_doctor = data.notas_doctor
    if data.motivo is not None:
        cita.motivo = data.motivo
    # Asignación explícita de doctor (admin puede asignar a cualquiera)
    if data.doctor_id is not None:
        cita.doctor_id = data.doctor_id

    if data.fecha_solicitada:
        try:
            fecha_str = data.fecha_solicitada.replace('T', ' ')
            cita.fecha_solicitada = datetime.strptime(fecha_str[:16], '%Y-%m-%d %H:%M')
        except ValueError:
            pass

    db.commit()
    db.refresh(cita)

    registrar_desde_request(
        db, request, doctor, Accion.EDITAR, Recurso.CITA,
        recurso_id=str(cita_id),
        detalle={
            "estado_anterior": estado_anterior,
            "estado_nuevo": cita.estado,
            "doctor_asignado": str(cita.doctor_id) if cita.doctor_id else None,
        },
    )
    return cita
