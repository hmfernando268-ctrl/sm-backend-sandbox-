"""
Genera una ENCRYPTION_KEY nueva y la muestra para agregar al .env.
También ofrece migrar los datos existentes sin cifrar.

Uso:
  python generar_clave_cifrado.py           # genera clave nueva
  python generar_clave_cifrado.py --migrar  # cifra datos existentes en BD
"""
import sys
import argparse


def generar_clave():
    from cryptography.fernet import Fernet
    clave = Fernet.generate_key().decode()
    print("\n✅ Clave generada. Agrega esta línea a tu .env:\n")
    print(f"ENCRYPTION_KEY={clave}\n")
    print("⚠️  IMPORTANTE:")
    print("  • Guarda esta clave en un lugar seguro")
    print("  • Si la pierdes, los datos cifrados serán irrecuperables")
    print("  • No la compartas ni la subas a Git")
    return clave


def migrar_datos_existentes():
    """Cifra los campos sensibles de registros existentes sin cifrar."""
    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    from app.db.session import SessionLocal
    from app.models.paciente import Paciente
    from app.services.crypto_service import cifrar, esta_cifrado

    db = SessionLocal()
    try:
        pacientes = db.query(Paciente).all()
        migrados = 0

        for p in pacientes:
            cambios = False
            # Cifrar alergias si no están cifradas
            if p._alergias and not esta_cifrado(p._alergias):
                p._alergias = cifrar(p._alergias)
                cambios = True
            # Cifrar notas si no están cifradas
            if p._notas_generales and not esta_cifrado(p._notas_generales):
                p._notas_generales = cifrar(p._notas_generales)
                cambios = True
            if cambios:
                migrados += 1

        db.commit()
        print(f"✅ Migración completada: {migrados} pacientes cifrados")
        print(f"   Total pacientes: {len(pacientes)}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrar", action="store_true")
    args = parser.parse_args()

    if args.migrar:
        migrar_datos_existentes()
    else:
        generar_clave()
