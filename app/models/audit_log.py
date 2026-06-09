import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class AuditLog(Base):
    """Registro de todas las acciones realizadas en el sistema."""
    __tablename__ = "audit_log"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultorio_id  = Column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=True)
    doctor_id       = Column(UUID(as_uuid=True), ForeignKey("doctores.id"), nullable=True)
    doctor_email    = Column(String(200))
    accion          = Column(String(50), nullable=False)
    recurso         = Column(String(50), nullable=False)
    recurso_id      = Column(UUID(as_uuid=True), nullable=True)
    detalle         = Column(Text)
    ip_address      = Column(String(50))
    user_agent      = Column(Text)
    created_at      = Column(DateTime, default=datetime.utcnow)
