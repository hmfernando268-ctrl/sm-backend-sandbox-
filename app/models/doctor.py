import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Doctor(Base):
    """Doctor dentro de un consultorio. Puede ser admin o doctor regular."""
    __tablename__ = "doctores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultorio_id = Column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=False)
    nombre = Column(String(200), nullable=False)
    apellido = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(500), nullable=False)
    cedula_profesional = Column(String(100))
    especialidad = Column(String(200))
    firma_url = Column(String(500))       # Imagen de firma para recetas
    rol = Column(String(20), default="doctor")  # admin | doctor
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    consultorio = relationship("Consultorio", back_populates="doctores")
    citas = relationship("Cita", back_populates="doctor")
    recetas = relationship("Receta", back_populates="doctor")
