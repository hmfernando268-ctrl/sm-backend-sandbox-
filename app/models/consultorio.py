import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Consultorio(Base):
    """Un consultorio = un tenant independiente en el sistema."""
    __tablename__ = "consultorios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # Para URLs
    telefono = Column(String(20))
    direccion = Column(Text)
    logo_url = Column(String(500))
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    doctores = relationship("Doctor", back_populates="consultorio")
    pacientes = relationship("Paciente", back_populates="consultorio")
