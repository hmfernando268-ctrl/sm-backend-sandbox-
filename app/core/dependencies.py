from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token

bearer_scheme = HTTPBearer()

def get_current_doctor(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    from app.models.doctor import Doctor
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    doctor_id = payload.get("sub")
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.activo == True).first()
    if not doctor:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Doctor no encontrado")
    return doctor

def require_admin(doctor=Depends(get_current_doctor)):
    if doctor.rol != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requiere rol admin")
    return doctor
