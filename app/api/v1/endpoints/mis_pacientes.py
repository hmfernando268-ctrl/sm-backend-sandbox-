"""
Endpoint 'Mis pacientes' — la cartera personal de cada doctor.
Combina: pacientes de cabecera + pacientes atendidos en citas.
Se agrega al router de pacientes existente.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.db.session import get_db
from app.core.dependencies import get_current_doctor
from app.models.paciente import Paciente
from app.models.cita import Cita

router = APIRouter(prefix="/mis-pacientes", tags=["Mis Pacientes"])


@router.get("/")
def mis_pacientes(
    db: Session = Depends(get_db),
    doctor=Depends(get_current_doctor),
):
    """
    Devuelve los pacientes del doctor autenticado:
    - Aquellos donde es doctor de cabecera
    - Aquellos a quienes ha atendido en al menos una cita
    Cada paciente aparece una sola vez con sus relaciones marcadas.
    """
    # Pacientes de cabecera
    cabecera_ids = {
        str(p.id) for p in db.query(Paciente.id).filter(
            Paciente.doctor_cabecera_id == doctor.id,
            Paciente.consultorio_id == doctor.consultorio_id,
        ).all()
    }

    # Pacientes atendidos en citas (doctor asignado)
    citas = db.query(Cita).filter(
        Cita.doctor_id == doctor.id,
        Cita.consultorio_id == doctor.consultorio_id,
    ).all()

    # Conteo de citas atendidas y última fecha por paciente
    atendidos: dict = {}
    for c in citas:
        pid = str(c.paciente_id)
        if pid not in atendidos:
            atendidos[pid] = {"total_citas": 0, "ultima_cita": None}
        atendidos[pid]["total_citas"] += 1
        fecha = c.fecha_solicitada
        if atendidos[pid]["ultima_cita"] is None or fecha > atendidos[pid]["ultima_cita"]:
            atendidos[pid]["ultima_cita"] = fecha

    # Unión de ambos conjuntos
    todos_ids = cabecera_ids | set(atendidos.keys())
    if not todos_ids:
        return []

    pacientes = db.query(Paciente).filter(
        Paciente.id.in_(todos_ids),
        Paciente.activo == True,
    ).all()

    resultado = []
    for p in pacientes:
        pid = str(p.id)
        info_citas = atendidos.get(pid, {})
        resultado.append({
            "id": pid,
            "nombre": p.nombre,
            "apellido": p.apellido,
            "email": p.email,
            "telefono": p.telefono,
            "alergias": p.alergias,
            "es_cabecera": pid in cabecera_ids,
            "total_citas_atendidas": info_citas.get("total_citas", 0),
            "ultima_cita": info_citas["ultima_cita"].isoformat() if info_citas.get("ultima_cita") else None,
        })

    # Ordenar: primero cabecera, luego por más citas atendidas
    resultado.sort(key=lambda x: (not x["es_cabecera"], -x["total_citas_atendidas"]))
    return resultado
