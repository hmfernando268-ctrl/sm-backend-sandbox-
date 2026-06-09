from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid

class Medicamento(BaseModel):
    nombre: str
    dosis: str
    frecuencia: str
    duracion: Optional[str] = None

class RecetaCreate(BaseModel):
    paciente_id: uuid.UUID
    cita_id: Optional[uuid.UUID] = None
    diagnostico: str
    medicamentos: List[Medicamento]
    indicaciones: Optional[str] = None

class RecetaResponse(BaseModel):
    id: uuid.UUID
    doctor_id: uuid.UUID
    paciente_id: uuid.UUID
    diagnostico: str
    medicamentos: str
    indicaciones: Optional[str]
    pdf_url: Optional[str]
    enviada: bool
    created_at: datetime

    class Config:
        from_attributes = True
