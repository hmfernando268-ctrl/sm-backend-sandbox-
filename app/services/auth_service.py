from sqlalchemy.orm import Session
from app.models.doctor import Doctor
from app.core.security import verify_password, create_access_token, hash_password

def authenticate_doctor(db: Session, email: str, password: str):
    doctor = db.query(Doctor).filter(Doctor.email == email, Doctor.activo == True).first()
    if not doctor or not verify_password(password, doctor.hashed_password):
        return None
    return doctor

def build_token(doctor: Doctor) -> dict:
    token = create_access_token({
        "sub": str(doctor.id),
        "consultorio_id": str(doctor.consultorio_id),
        "rol": doctor.rol,
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "doctor_id": str(doctor.id),
        "consultorio_id": str(doctor.consultorio_id),
        "rol": doctor.rol,
    }
