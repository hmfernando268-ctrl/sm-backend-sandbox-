from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.paciente import Paciente
from app.schemas.paciente import PacienteCreate, PacienteUpdate, PacienteResponse
from app.services.audit_service import registrar_desde_request, Accion, Recurso

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])

@router.get("/", response_model=List[PacienteResponse])
def listar_pacientes(
    skip: int = 0,
    limit: int = 50,
    request: Request = None,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    pacientes = (
        db.query(Paciente)
        .filter(Paciente.consultorio_id == doctor.consultorio_id, Paciente.activo == True)
        .offset(skip).limit(limit).all()
    )
    return pacientes

@router.post("/", response_model=PacienteResponse, status_code=201)
def crear_paciente(
    data: PacienteCreate,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    paciente = Paciente(**data.model_dump(), consultorio_id=doctor.consultorio_id)
    db.add(paciente)
    db.commit()
    db.refresh(paciente)

    registrar_desde_request(
        db, request, doctor, Accion.CREAR, Recurso.PACIENTE,
        recurso_id=str(paciente.id),
        detalle={"nombre": f"{paciente.nombre} {paciente.apellido}", "email": paciente.email},
    )
    return paciente

@router.get("/{paciente_id}", response_model=PacienteResponse)
def obtener_paciente(
    paciente_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    paciente = db.query(Paciente).filter(
        Paciente.id == paciente_id,
        Paciente.consultorio_id == doctor.consultorio_id,
    ).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    registrar_desde_request(
        db, request, doctor, Accion.VER, Recurso.PACIENTE,
        recurso_id=str(paciente_id),
        detalle={"nombre": f"{paciente.nombre} {paciente.apellido}"},
    )
    return paciente

@router.patch("/{paciente_id}", response_model=PacienteResponse)
def actualizar_paciente(
    paciente_id: uuid.UUID,
    data: PacienteUpdate,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    paciente = db.query(Paciente).filter(
        Paciente.id == paciente_id,
        Paciente.consultorio_id == doctor.consultorio_id,
    ).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    campos_editados = [k for k, v in data.model_dump(exclude_unset=True).items()]
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(paciente, field, value)
    db.commit()
    db.refresh(paciente)

    registrar_desde_request(
        db, request, doctor, Accion.EDITAR, Recurso.PACIENTE,
        recurso_id=str(paciente_id),
        detalle={"campos": campos_editados},
    )
    return paciente
