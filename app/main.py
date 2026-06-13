from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
# Importar modelos aquí para que SQLAlchemy los registre al arrancar
import app.models  # noqa: F401
from app.api.v1.router import api_router
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sistema-medico")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
# Lee ALLOWED_ORIGINS del entorno (separados por coma si hay varios).
# Siempre incluye localhost para desarrollo local.
origenes = ["http://localhost:3000", "http://127.0.0.1:3000"]
if settings.ALLOWED_ORIGINS:
    # Permite uno o varios orígenes separados por coma
    extra = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    origenes.extend(extra)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response

@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )

app.include_router(api_router)

@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
def health():
    return {"status": "ok", "version": settings.APP_VERSION}
