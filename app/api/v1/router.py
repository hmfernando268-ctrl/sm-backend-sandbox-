from fastapi import APIRouter
from app.api.v1.endpoints import auth, pacientes, citas, recetas, dashboard, auditoria, doctores, mis_pacientes

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(pacientes.router)
api_router.include_router(citas.router)
api_router.include_router(recetas.router)
api_router.include_router(dashboard.router)
api_router.include_router(auditoria.router)
api_router.include_router(doctores.router)
api_router.include_router(mis_pacientes.router)