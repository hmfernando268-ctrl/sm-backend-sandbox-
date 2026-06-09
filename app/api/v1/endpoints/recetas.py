import json
import uuid
import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.receta import Receta
from app.models.paciente import Paciente
from app.schemas.receta import RecetaCreate, RecetaResponse
from app.services.pdf_service import generar_receta_html, html_a_pdf
from app.services.webhook_service import notificar_receta_lista
from app.services.audit_service import registrar_desde_request, Accion, Recurso

router = APIRouter(prefix="/recetas", tags=["Recetas"])


@router.get("/", response_model=List[RecetaResponse])
def listar_recetas(
    paciente_id: str = None,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    q = db.query(Receta).filter(Receta.consultorio_id == doctor.consultorio_id)
    if paciente_id:
        q = q.filter(Receta.paciente_id == paciente_id)
    return q.order_by(Receta.created_at.desc()).all()


@router.post("/", response_model=RecetaResponse, status_code=201)
def crear_receta(
    data: RecetaCreate,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    meds_json = json.dumps([m.model_dump() for m in data.medicamentos], ensure_ascii=False)
    receta = Receta(
        consultorio_id=doctor.consultorio_id,
        doctor_id=doctor.id,
        paciente_id=data.paciente_id,
        cita_id=data.cita_id,
        diagnostico=data.diagnostico,
        medicamentos=meds_json,
        indicaciones=data.indicaciones,
    )
    db.add(receta)
    db.commit()
    db.refresh(receta)

    registrar_desde_request(
        db, request, doctor, Accion.CREAR, Recurso.RECETA,
        recurso_id=str(receta.id),
        detalle={
            "paciente_id": str(data.paciente_id),
            "diagnostico": data.diagnostico[:60],
            "num_medicamentos": len(data.medicamentos),
        },
    )
    return receta


@router.get("/{receta_id}/pdf")
def descargar_pdf(
    receta_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    receta = db.query(Receta).filter(
        Receta.id == receta_id,
        Receta.consultorio_id == doctor.consultorio_id,
    ).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    paciente = db.query(Paciente).filter(Paciente.id == receta.paciente_id).first()
    medicamentos = json.loads(receta.medicamentos)

    datos = generar_receta_html(doctor, paciente, receta, medicamentos)
    pdf_bytes = html_a_pdf(datos)

    registrar_desde_request(
        db, request, doctor, Accion.GENERAR_PDF, Recurso.RECETA,
        recurso_id=str(receta_id),
        detalle={"paciente_id": str(receta.paciente_id)},
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="receta-{str(receta_id)[:8]}.pdf"'}
    )


@router.post("/{receta_id}/enviar")
async def enviar_receta(
    receta_id: uuid.UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    receta = db.query(Receta).filter(
        Receta.id == receta_id,
        Receta.consultorio_id == doctor.consultorio_id,
    ).first()
    if not receta:
        raise HTTPException(status_code=404, detail="Receta no encontrada")

    paciente = db.query(Paciente).filter(Paciente.id == receta.paciente_id).first()
    medicamentos = json.loads(receta.medicamentos)

    datos = generar_receta_html(doctor, paciente, receta, medicamentos)
    pdf_bytes = html_a_pdf(datos)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")

    canal = "whatsapp" if paciente.telefono else "email"

    background_tasks.add_task(
        notificar_receta_lista,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        paciente_telefono=paciente.telefono or "",
        paciente_email=paciente.email or "",
        receta_id=str(receta_id),
        pdf_b64=pdf_b64,
        doctor_nombre=f"Dr. {doctor.nombre} {doctor.apellido}",
        consultorio_nombre=doctor.consultorio.nombre,
    )

    receta.enviada = True
    receta.fecha_envio = datetime.utcnow()
    db.commit()

    registrar_desde_request(
        db, request, doctor, Accion.ENVIAR, Recurso.RECETA,
        recurso_id=str(receta_id),
        detalle={
            "canal": canal,
            "paciente": f"{paciente.nombre} {paciente.apellido}",
        },
    )

    return {
        "mensaje": "Receta enviada correctamente",
        "receta_id": str(receta_id),
        "paciente": f"{paciente.nombre} {paciente.apellido}",
        "canal": canal,
    }
