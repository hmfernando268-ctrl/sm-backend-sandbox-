from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

# psycopg v3 usa "postgresql+psycopg://" — corregimos el prefijo si viene el viejo
_db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Sesión básica sin RLS. Usada solo en login (aún no hay doctor autenticado)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def set_rls_context(db: Session, doctor_id: str, consultorio_id: str, rol: str) -> None:
    """
    Inyecta las variables de sesión que leen las políticas RLS de Supabase.
    SET LOCAL aplica solo a la transacción actual — se limpia automáticamente al cerrar.
    """
    db.execute(text("SET LOCAL app.doctor_id      = :v"), {"v": doctor_id})
    db.execute(text("SET LOCAL app.consultorio_id = :v"), {"v": consultorio_id})
    db.execute(text("SET LOCAL app.rol            = :v"), {"v": rol})
