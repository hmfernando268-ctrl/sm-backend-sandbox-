import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Receta(Base):
    """Receta médica generada por el doctor."""
    __tablename__ = "recetas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultorio_id = Column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctores.id"), nullable=False)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    cita_id = Column(UUID(as_uuid=True), ForeignKey("citas.id"))
    diagnostico = Column(Text, nullable=False)
    medicamentos = Column(Text, nullable=False)  # JSON string: [{nombre, dosis, frecuencia}]
    indicaciones = Column(Text)
    pdf_url = Column(String(500))        # URL en Supabase Storage
    enviada = Column(Boolean, default=False)
    fecha_envio = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    doctor = relationship("Doctor", back_populates="recetas")
    paciente = relationship("Paciente", back_populates="recetas")
    cita = relationship("Cita", back_populates="recetas")
