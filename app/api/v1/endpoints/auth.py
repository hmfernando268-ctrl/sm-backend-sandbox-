from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import authenticate_doctor, build_token
from app.services.audit_service import registrar, Accion, Recurso
from app.middleware.rate_limit import rate_limit_login

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Rate limiting: máximo 5 intentos por minuto
    rate_limit_login(request)

    doctor = authenticate_doctor(db, data.email, data.password)
    if not doctor:
        registrar(
            db=db, accion="LOGIN_FALLIDO", recurso=Recurso.SISTEMA,
            doctor_email=data.email,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            detalle={"motivo": "credenciales_incorrectas"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    registrar(
        db=db, accion=Accion.LOGIN, recurso=Recurso.SISTEMA,
        doctor_id=str(doctor.id),
        consultorio_id=str(doctor.consultorio_id),
        doctor_email=doctor.email,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return build_token(doctor)
