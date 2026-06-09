# Importar todos los modelos en orden de dependencia
# Esto garantiza que SQLAlchemy los registre antes de resolver las relaciones
from app.models.consultorio import Consultorio
from app.models.doctor import Doctor
from app.models.paciente import Paciente
from app.models.cita import Cita
from app.models.receta import Receta
from app.models.audit_log import AuditLog

__all__ = ["Consultorio", "Doctor", "Paciente", "Cita", "Receta"]
