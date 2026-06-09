import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum

class EstadoCita(str, enum.Enum):
    pendiente = "pendiente"
    confirmada = "confirmada"
    completada = "completada"
    cancelada = "cancelada"

class Cita(Base):
    """Solicitud de cita o consulta de un paciente."""
    __tablename__ = "citas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultorio_id = Column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=False)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctores.id"))
    fecha_solicitada = Column(DateTime, nullable=False)
    motivo = Column(Text, nullable=False)
    estado = Column(String(20), default=EstadoCita.pendiente)
    notas_doctor = Column(Text)        # Respuesta del doctor
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    paciente = relationship("Paciente", back_populates="citas")
    doctor = relationship("Doctor", back_populates="citas")
    recetas = relationship("Receta", back_populates="cita")
