# -*- coding: utf-8 -*-
"""
Seed Final para Demo del Tribunal -- RutAIGeoProxi.

ESTE SCRIPT:
1. Limpia toda la base de datos (BORRA TODO).
2. Crea 2 Admins, 2 Talleres, 2 Clientes.
3. Configura talleres, vehículos y técnicos.
4. Crea incidentes en diferentes estados para probar el flujo E2E.

Contraseña para todos: Password123
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Fix encoding para consolas Windows
if hasattr(sys.stdout, 'buffer') and (sys.stdout.encoding or '').upper() not in ('UTF-8', 'UTF8'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

directorio_actual = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, directorio_actual)
load_dotenv(os.path.join(directorio_actual, ".env"))

from sqlalchemy.orm import Session
from sqlalchemy import text

# URL de Producción en Render
RENDER_DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(RENDER_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
from app.shared.database import Base
from app.shared.security import get_password_hash
from app.modules.p1_usuarios.models import Usuario, Vehiculo
from app.modules.p2_incidentes.models import Incidente, ClasificacionIncidente
from app.modules.p3_talleres.models import Taller, Tecnico, SolicitudServicio
from app.modules.p4_asignacion.models import Asignacion
from app.modules.p5_pagos.models import Pago, Notificacion

def clear_db(db: Session):
    print("\n[CLEAN] Intentando limpiar tablas existentes...")
    try:
        # En Postgres con SCHEMA limpio, esto puede fallar si no hay tablas, lo ignoramos.
        db.execute(text("DELETE FROM notificaciones"))
        db.execute(text("DELETE FROM pagos"))
        db.execute(text("DELETE FROM solicitudes_servicio"))
        db.execute(text("DELETE FROM asignaciones"))
        db.execute(text("DELETE FROM clasificaciones_incidente"))
        db.execute(text("DELETE FROM incidentes"))
        db.execute(text("DELETE FROM tecnicos"))
        db.execute(text("DELETE FROM talleres"))
        db.execute(text("DELETE FROM vehiculos"))
        db.execute(text("DELETE FROM usuarios"))
        db.commit()
        print("  [OK] Tablas limpias.")
    except Exception as e:
        print(f"  [SKIP] No se pudieron limpiar algunas tablas (posiblemente ya borradas): {e}")
        db.rollback()

def create_user(db: Session, email: str, nombre: str, rol: str) -> Usuario:
    u = Usuario(
        nombre=nombre,
        email=email,
        hashed_password=get_password_hash("Password123"),
        rol=rol,
        esta_activo=True,
        intentos_fallidos=0
    )
    db.add(u)
    db.flush()
    print(f"  [USER] Creado: {email} ({rol})")
    return u

def seed():
    print("\n[SCHEMA] Creando tablas en Render...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("\n" + "="*60)
        print("🚀 SEED FINAL - RUTAIGEOPROXI DEMO TRIBUNAL")
        print("="*60)

        clear_db(db)

        # ── 1. Usuarios Admins ─────────────────────────────────────────
        print("\n[1] Creando Administradores...")
        admin1 = create_user(db, "xdreicarlos@gmail.com", "Admin Central Carlos", "admin")
        admin2 = create_user(db, "joetoe250@gmail.com", "Admin Auditor Joe", "admin")

        # ── 2. Usuarios Talleres ────────────────────────────────────────
        print("\n[2] Creando Talleres...")
        u_taller1 = create_user(db, "fitgo61@gmail.com", "Propietario El Rayo", "taller")
        u_taller2 = create_user(db, "etsech67@gmail.com", "Propietario Motores Pro", "taller")

        taller1 = Taller(
            usuario_propietario_id=u_taller1.id,
            nombre="Taller El Rayo",
            direccion="Av. Arce #123, La Paz",
            latitud=-16.5000, longitud=-68.1300,
            telefono="+59170011223",
            email="fitgo61@gmail.com",
            especialidades=["mecanico", "electrico", "neumaticos"]
        )
        taller2 = Taller(
            usuario_propietario_id=u_taller2.id,
            nombre="Motores Pro",
            direccion="Calle 21 de Calacoto, La Paz",
            latitud=-16.5400, longitud=-68.0900,
            telefono="+59170044556",
            email="etsech67@gmail.com",
            especialidades=["carroceria", "mecanico", "emergencia"]
        )
        db.add_all([taller1, taller2])
        db.flush()

        tec1 = Tecnico(
            taller_id=taller1.id,
            nombre="Roberto 'Turbo' Ramos",
            especialidad="mecanico",
            latitud=-16.5010, longitud=-68.1310, # Cerca del taller
            esta_disponible=True
        )
        tec2 = Tecnico(
            taller_id=taller2.id,
            nombre="Mario 'Llave' Lopez",
            especialidad="electrico",
            latitud=-16.5410, longitud=-68.0910,
            esta_disponible=True
        )
        db.add_all([tec1, tec2])
        db.flush()

        # ── 3. Usuarios Clientes ────────────────────────────────────────
        print("\n[3] Creando Clientes...")
        cliente1 = create_user(db, "ramosvargabrayan@gmail.com", "Brayan Ramos", "cliente")
        cliente2 = create_user(db, "joelramostrbj@gmail.com", "Joel Ramos", "cliente")

        v1 = Vehiculo(usuario_id=cliente1.id, marca="Toyota", modelo="Hilux", placa="1234-ABC", anio=2022, color="Blanco")
        v2 = Vehiculo(usuario_id=cliente2.id, marca="Suzuki", modelo="Swift", placa="5678-XYZ", anio=2021, color="Rojo")
        db.add_all([v1, v2])
        db.flush()

        # ── 4. Escenario de Prueba 1: Incidente en Proceso (Seguimiento) ─
        print("\n[4] Creando Escenario: Incidente en Proceso...")
        inc1 = Incidente(
            usuario_id=cliente1.id,
            titulo="Falla de motor en El Prado",
            descripcion="El auto se apagó de repente y sale humo blanco.",
            estado="en_proceso",
            latitud=-16.4980, longitud=-68.1320,
            direccion="Av. 16 de Julio (El Prado), La Paz",
            severidad="grave",
            categoria="mecanico"
        )
        db.add(inc1)
        db.flush()

        # Clasificación IA
        db.add(ClasificacionIncidente(
            incidente_id=inc1.id,
            categoria="mecanico",
            severidad="grave",
            confianza=0.98,
            razonamiento="Humo blanco y apagado repentino indican falla mecánica severa.",
            metodo="reglas"
        ))

        # Asignación y Solicitud
        db.add(Asignacion(incidente_id=inc1.id, taller_id=taller1.id, distancia_km=0.5, puntaje=95.0))
        db.add(SolicitudServicio(
            incidente_id=inc1.id,
            taller_id=taller1.id,
            tecnico_id=tec1.id,
            estado="proceso",
            notas="Técnico Roberto en camino. Tiempo estimado 5 min."
        ))

        # ── 5. Escenario de Prueba 2: Incidente Nuevo (Para Asignar) ───
        print("\n[5] Creando Escenario: Incidente Nuevo...")
        inc2 = Incidente(
            usuario_id=cliente2.id,
            titulo="Llanta pinchada en la autopista",
            descripcion="Necesito auxilio para cambiar la llanta de auxilio.",
            estado="nuevo",
            latitud=-16.4800, longitud=-68.1500,
            direccion="Autopista La Paz-El Alto, km 5",
        )
        db.add(inc2)
        db.flush()

        db.commit()

        print("\n" + "="*60)
        print("✅ SEED COMPLETADO - SISTEMA LISTO PARA PRUEBAS")
        print("="*60)
        print("\nCREDENCIALES (Password: Password123):")
        print(f"  [ADMIN]  {admin1.email}")
        print(f"  [ADMIN]  {admin2.email}")
        print(f"  [TALLER] {u_taller1.email} (Taller El Rayo)")
        print(f"  [TALLER] {u_taller2.email} (Motores Pro)")
        print(f"  [CLIENTE] {cliente1.email} (Brayan)")
        print(f"  [CLIENTE] {cliente2.email} (Joel)")
        
        print("\nFLUJO SUGERIDO PARA LA DEMO:")
        print("  1. Entra como Admin con xdreicarlos@gmail.com")
        print(f"  2. Verás un incidente NUEVO (#{inc2.id}) listo para asignar.")
        print("  3. Asigna el taller 'Motores Pro'.")
        print("  4. Entra como Taller con etsech67@gmail.com y acepta el servicio.")
        print("  5. Entra como Cliente con ramosvargabrayan@gmail.com en la App.")
        print(f"  6. Verás tu incidente en proceso (#{inc1.id}) y verás al técnico moviéndose en el mapa.")
        print("  7. Cuando el Taller termine el servicio, el Cliente paga y verás el desglose del 10%.")

    except Exception as e:
        print(f"\n[ERR] Error durante el seed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
