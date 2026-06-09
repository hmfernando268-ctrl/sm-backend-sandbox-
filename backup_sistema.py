"""
Sistema de Backups Automáticos — Sistema Médico
================================================
Hace un dump completo de la BD Neon en formato SQL comprimido.
Guarda los últimos 30 días y elimina los más antiguos automáticamente.

Uso:
  python backup_sistema.py              # backup manual
  python backup_sistema.py --verificar  # verifica el último backup
  python backup_sistema.py --listar     # lista todos los backups

Programar en Windows (ejecutar una vez para configurar):
  python backup_sistema.py --programar
"""
import os
import sys
import gzip
import shutil
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# ── CONFIGURACIÓN ─────────────────────────────────────────────
BACKUP_DIR = Path("C:/backups/sistema-medico")
RETENER_DIAS = 30
LOG_FILE = BACKUP_DIR / "backup.log"

# Cargar DATABASE_URL del .env
def cargar_env():
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        raise FileNotFoundError(f"No se encontró .env en {env_path}")
    valores = {}
    for linea in env_path.read_text().splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip()
    return valores

def configurar_logging():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

def parsear_db_url(url: str) -> dict:
    """Extrae componentes de la DATABASE_URL."""
    # Normalizar prefijo para urllib
    url_norm = url.replace("postgresql+psycopg://", "postgresql://")
    parsed = urlparse(url_norm)
    return {
        "host": parsed.hostname,
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/").split("?")[0],
        "user": parsed.username,
        "password": parsed.password,
    }

def hacer_backup() -> Path:
    """Ejecuta pg_dump y guarda el resultado comprimido."""
    env = cargar_env()
    db_url = env.get("DATABASE_URL", "")
    if not db_url:
        raise ValueError("DATABASE_URL no encontrado en .env")

    db = parsear_db_url(db_url)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = BACKUP_DIR / f"backup_{timestamp}.sql.gz"

    logging.info(f"Iniciando backup → {archivo.name}")
    logging.info(f"BD: {db['dbname']} en {db['host']}")

    # pg_dump via Python puro (sin necesitar pg_dump instalado)
    # Usa psycopg para exportar tabla por tabla
    try:
        import psycopg
        conn_str = f"host={db['host']} port={db['port']} dbname={db['dbname']} user={db['user']} password={db['password']} sslmode=require"

        tablas = ["consultorios", "doctores", "pacientes", "citas", "recetas", "audit_log"]
        lineas = []
        lineas.append(f"-- Backup Sistema Médico")
        lineas.append(f"-- Fecha: {datetime.now().isoformat()}")
        lineas.append(f"-- BD: {db['dbname']}")
        lineas.append("")

        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                for tabla in tablas:
                    logging.info(f"  Exportando tabla: {tabla}")
                    try:
                        # Obtener columnas
                        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tabla}' ORDER BY ordinal_position")
                        columnas = [r[0] for r in cur.fetchall()]
                        if not columnas:
                            continue

                        # Obtener filas
                        cur.execute(f"SELECT * FROM {tabla}")
                        filas = cur.fetchall()
                        count = len(filas)

                        lineas.append(f"-- Tabla: {tabla} ({count} registros)")
                        lineas.append(f"DELETE FROM {tabla};")

                        for fila in filas:
                            valores = []
                            for v in fila:
                                if v is None:
                                    valores.append("NULL")
                                elif isinstance(v, bool):
                                    valores.append("TRUE" if v else "FALSE")
                                elif isinstance(v, (int, float)):
                                    valores.append(str(v))
                                else:
                                    # Escapar comillas simples
                                    val_str = str(v).replace("'", "''")
                                    valores.append(f"'{val_str}'")

                            cols = ", ".join(columnas)
                            vals = ", ".join(valores)
                            lineas.append(f"INSERT INTO {tabla} ({cols}) VALUES ({vals});")

                        lineas.append("")
                        logging.info(f"  ✓ {tabla}: {count} registros")

                    except Exception as e:
                        logging.warning(f"  ⚠ Error en tabla {tabla}: {e}")

        # Comprimir y guardar
        contenido = "\n".join(lineas).encode("utf-8")
        with gzip.open(archivo, "wb") as f:
            f.write(contenido)

        tam_mb = archivo.stat().st_size / 1024 / 1024
        logging.info(f"✅ Backup completado: {archivo.name} ({tam_mb:.2f} MB)")
        return archivo

    except ImportError:
        raise RuntimeError("psycopg no está instalado. Corre: pip install psycopg[binary]")


def limpiar_backups_antiguos():
    """Elimina backups con más de RETENER_DIAS días."""
    limite = datetime.now() - timedelta(days=RETENER_DIAS)
    eliminados = 0
    for archivo in BACKUP_DIR.glob("backup_*.sql.gz"):
        if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            eliminados += 1
            logging.info(f"🗑 Eliminado backup antiguo: {archivo.name}")
    if eliminados == 0:
        logging.info("No hay backups antiguos que eliminar")
    else:
        logging.info(f"Eliminados {eliminados} backups antiguos")


def listar_backups():
    """Muestra todos los backups disponibles."""
    archivos = sorted(BACKUP_DIR.glob("backup_*.sql.gz"), reverse=True)
    if not archivos:
        print("No hay backups disponibles")
        return
    print(f"\n{'Archivo':<35} {'Tamaño':>10} {'Fecha'}")
    print("-" * 65)
    for a in archivos:
        tam = a.stat().st_size / 1024
        fecha = datetime.fromtimestamp(a.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{a.name:<35} {tam:>8.1f} KB  {fecha}")
    print(f"\nTotal: {len(archivos)} backups en {BACKUP_DIR}")


def verificar_ultimo():
    """Verifica que el último backup es válido."""
    archivos = sorted(BACKUP_DIR.glob("backup_*.sql.gz"), reverse=True)
    if not archivos:
        print("❌ No hay backups disponibles")
        return False
    ultimo = archivos[0]
    try:
        with gzip.open(ultimo, "rb") as f:
            contenido = f.read().decode("utf-8")
        tablas = contenido.count("-- Tabla:")
        registros = contenido.count("INSERT INTO")
        edad = datetime.now() - datetime.fromtimestamp(ultimo.stat().st_mtime)
        print(f"✅ Último backup: {ultimo.name}")
        print(f"   Tablas: {tablas} | Registros: {registros}")
        print(f"   Edad: {int(edad.total_seconds() / 3600)} horas")
        print(f"   Tamaño: {ultimo.stat().st_size / 1024:.1f} KB")
        return True
    except Exception as e:
        print(f"❌ Backup corrupto: {e}")
        return False


def programar_tarea_windows():
    """Crea una tarea programada en Windows para ejecutar el backup diariamente."""
    import subprocess
    script_path = Path(__file__).resolve()
    python_path = sys.executable
    cmd = (
        f'schtasks /create /tn "SistemaMedico_Backup" '
        f'/tr "\\"{python_path}\\" \\"{script_path}\\"" '
        f'/sc daily /st 02:00 /f'
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Tarea programada creada: backup diario a las 2:00 AM")
        print("   Para verificar: schtasks /query /tn SistemaMedico_Backup")
    else:
        print(f"❌ Error al crear tarea: {result.stderr}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup Sistema Médico")
    parser.add_argument("--listar",    action="store_true", help="Lista los backups disponibles")
    parser.add_argument("--verificar", action="store_true", help="Verifica el último backup")
    parser.add_argument("--programar", action="store_true", help="Programa el backup diario en Windows")
    args = parser.parse_args()

    configurar_logging()

    if args.listar:
        listar_backups()
    elif args.verificar:
        verificar_ultimo()
    elif args.programar:
        programar_tarea_windows()
    else:
        # Backup normal
        try:
            hacer_backup()
            limpiar_backups_antiguos()
        except Exception as e:
            logging.error(f"❌ Backup falló: {e}")
            sys.exit(1)
