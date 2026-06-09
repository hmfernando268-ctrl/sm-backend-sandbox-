"""
Gestión de doctores — solo accesible para admins del consultorio.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import uuid

from app.db.session import get_db
from app.core.dependencies import get_current_doctor, require_admin
from app.core.security import hash_password
from app.models.doctor import Doctor
from app.services.audit_service import registrar_desde_request, Accion, Recurso

router = APIRouter(prefix="/doctores", tags=["Doctores"])


# ── SCHEMAS ───────────────────────────────────────────────────
class DoctorCreate(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    password: str
    cedula_profesional: Optional[str] = None
    especialidad: Optional[str] = None
    rol: str = "doctor"  # doctor | admin

class DoctorUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    cedula_profesional: Optional[str] = None
    especialidad: Optional[str] = None
    activo: Optional[bool] = None
    rol: Optional[str] = None

class DoctorResponse(BaseModel):
    id: uuid.UUID
    consultorio_id: uuid.UUID
    nombre: str
    apellido: str
    email: str
    cedula_profesional: Optional[str] = None
    especialidad: Optional[str] = None
    rol: str
    activo: bool

    class Config:
        from_attributes = True


# ── ENDPOINTS ─────────────────────────────────────────────────
@router.get("/", response_model=List[DoctorResponse])
def listar_doctores(
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """Lista todos los doctores del consultorio."""
    return db.query(Doctor).filter(
        Doctor.consultorio_id == doctor.consultorio_id
    ).order_by(Doctor.nombre).all()


@router.post("/", response_model=DoctorResponse, status_code=201)
def crear_doctor(
    data: DoctorCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Crea un nuevo doctor en el consultorio. Solo admins."""
    # Verificar email único
    existe = db.query(Doctor).filter(Doctor.email == data.email).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un doctor con ese email")

    nuevo = Doctor(
        consultorio_id=admin.consultorio_id,
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        hashed_password=hash_password(data.password),
        cedula_profesional=data.cedula_profesional,
        especialidad=data.especialidad,
        rol=data.rol,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    registrar_desde_request(
        db, request, admin, Accion.CREAR, Recurso.DOCTOR,
        recurso_id=str(nuevo.id),
        detalle={"email": nuevo.email, "rol": nuevo.rol},
    )
    return nuevo


@router.patch("/{doctor_id}", response_model=DoctorResponse)
def actualizar_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Edita datos o desactiva un doctor. Solo admins."""
    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id,
        Doctor.consultorio_id == admin.consultorio_id,
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor no encontrado")

    # Un admin no puede desactivarse a sí mismo
    if data.activo == False and doctor_id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes desactivarte a ti mismo")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)
    db.commit()
    db.refresh(doctor)

    registrar_desde_request(
        db, request, admin, Accion.EDITAR, Recurso.DOCTOR,
        recurso_id=str(doctor_id),
        detalle={"campos": list(data.model_dump(exclude_unset=True).keys())},
    )
    return doctor
