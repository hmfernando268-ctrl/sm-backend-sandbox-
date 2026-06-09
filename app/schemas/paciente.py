from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
import uuid

class PacienteCreate(BaseModel):
    nombre: str
    apellido: str
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    alergias: Optional[str] = None
    notas_generales: Optional[str] = None
    doctor_cabecera_id: Optional[uuid.UUID] = None  # ← nuevo

class PacienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    alergias: Optional[str] = None
    notas_generales: Optional[str] = None
    doctor_cabecera_id: Optional[uuid.UUID] = None  # ← nuevo

class PacienteResponse(BaseModel):
    id: uuid.UUID
    consultorio_id: uuid.UUID
    doctor_cabecera_id: Optional[uuid.UUID] = None  # ← nuevo
    nombre: str
    apellido: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    alergias: Optional[str] = None
    notas_generales: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
