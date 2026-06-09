from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import uuid

class CitaCreate(BaseModel):
    paciente_id: uuid.UUID
    fecha_solicitada: datetime
    motivo: str

class CitaUpdate(BaseModel):
    doctor_id: Optional[uuid.UUID] = None
    estado: Optional[str] = None
    notas_doctor: Optional[str] = None
    fecha_solicitada: Optional[str] = None  # ← string para evitar conversión UTC
    motivo: Optional[str] = None

class CitaResponse(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    doctor_id: Optional[uuid.UUID]
    fecha_solicitada: datetime
    motivo: str
    estado: str
    notas_doctor: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
