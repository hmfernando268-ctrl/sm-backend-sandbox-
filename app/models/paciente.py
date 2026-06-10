import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Paciente(Base):
    """
    Paciente con campos sensibles cifrados automáticamente
    y doctor de cabecera asignado.
    """
    __tablename__ = "pacientes"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consultorio_id      = Column(UUID(as_uuid=True), ForeignKey("consultorios.id"), nullable=False)
    doctor_cabecera_id  = Column(UUID(as_uuid=True), ForeignKey("doctores.id"), nullable=True)
    nombre              = Column(String(200), nullable=False)
    apellido            = Column(String(200), nullable=False)
    email               = Column(String(200))
    telefono            = Column(String(20))
    fecha_nacimiento    = Column(Date)
    sexo                = Column(String(10))
    _alergias           = Column("alergias", Text)
    _notas_generales    = Column("notas_generales", Text)
    activo              = Column(Boolean, default=True)
    created_at          = Column(DateTime, default=datetime.utcnow)

    consultorio     = relationship("Consultorio", back_populates="pacientes")
    doctor_cabecera = relationship("Doctor", foreign_keys=[doctor_cabecera_id])
    citas           = relationship("Cita", back_populates="paciente")
    recetas         = relationship("Receta", back_populates="paciente")

    @property
    def alergias(self) -> str:
        from app.services.crypto_service import descifrar
        return descifrar(self._alergias)

    @alergias.setter
    def alergias(self, valor: str):
        from app.services.crypto_service import cifrar
        self._alergias = cifrar(valor)

    @property
    def notas_generales(self) -> str:
        from app.services.crypto_service import descifrar
        return descifrar(self._notas_generales)

    @notas_generales.setter
    def notas_generales(self, valor: str):
        from app.services.crypto_service import cifrar
        self._notas_generales = cifrar(valor)
