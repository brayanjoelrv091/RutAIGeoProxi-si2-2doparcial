# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URL de Producción en Render
RENDER_DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

engine = create_engine(RENDER_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Imports del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.shared.database import Base
from app.shared.security import get_password_hash
from app.modules.p1_usuarios.models import Usuario, Vehiculo
from app.modules.p2_incidentes.models import Incidente, ClasificacionIncidente
from app.modules.p3_talleres.models import Taller, Tecnico, SolicitudServicio
from app.modules.p4_asignacion.models import Asignacion
from app.modules.p5_pagos.models import Pago, Notificacion

def seed_v3():
    db = SessionLocal()
    try:
        print("\n[START] INICIANDO LIMPIEZA TOTAL PARA DEMO V3...")
        db.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
        db.commit()
        print("[OK] Base de datos vaciada por completo.")

        Base.metadata.create_all(bind=engine)
        print("[OK] Esquema recreado.")

        pw = "Password123"
        hashed = get_password_hash(pw)

        # 1. Crear el TRÍO DINÁMICO
        print("\n[1] Creando los 3 usuarios oficiales...")
        admin = Usuario(nombre="Admin Carlos", email="xdreicarlos@gmail.com", hashed_password=hashed, rol="admin", esta_activo=True)
        taller_u = Usuario(nombre="Dueño El Rayo", email="fitgo61@gmail.com", hashed_password=hashed, rol="taller", esta_activo=True)
        cliente = Usuario(nombre="Brayan Ramos", email="ramosvargabrayan@gmail.com", hashed_password=hashed, rol="cliente", esta_activo=True)
        db.add_all([admin, taller_u, cliente])
        db.flush()

        # 2. Configurar Taller y Técnico
        print("[2] Configurando Taller y Técnico...")
        taller = Taller(
            usuario_propietario_id=taller_u.id,
            nombre="Taller El Rayo",
            direccion="Av. Busch #123",
            latitud=-17.7833, longitud=-63.1821,
            telefono="+59170011223",
            email="fitgo61@gmail.com",
            especialidades=["mecanico", "electrico"]
        )
        db.add(taller)
        db.flush()

        tecnico = Tecnico(
            taller_id=taller.id,
            nombre="Roberto 'Turbo' Ramos",
            especialidad="mecanico",
            latitud=-17.7840, longitud=-63.1830,
            esta_disponible=True
        )
        db.add(tecnico)
        db.flush()

        # 3. Vehículo del Cliente
        v = Vehiculo(usuario_id=cliente.id, marca="Toyota", modelo="Hilux", placa="1234-ABC", anio=2022, color="Blanco")
        db.add(v)
        db.flush()

        # 4. ESCENARIO 1: TRACKING GPS (En Proceso)
        print("[3] Creando Escenario: Tracking GPS...")
        inc1 = Incidente(
            usuario_id=cliente.id,
            titulo="Falla de motor en el 2do Anillo",
            descripcion="El auto se detuvo y no enciende.",
            estado="en_proceso",
            latitud=-17.7850, longitud=-63.1850,
            direccion="Avenida Cristobal de Mendoza",
            categoria="mecanico", severidad="grave"
        )
        db.add(inc1)
        db.flush()
        
        db.add(Asignacion(incidente_id=inc1.id, taller_id=taller.id, distancia_km=0.8, puntaje=98.0))
        db.add(SolicitudServicio(
            incidente_id=inc1.id, taller_id=taller.id, tecnico_id=tecnico.id,
            estado="proceso", notas="Técnico Roberto está en camino."
        ))

        # 5. ESCENARIO 2: LISTO PARA PAGAR (Completado)
        print("[4] Creando Escenario: Listo para Pagar...")
        inc2 = Incidente(
            usuario_id=cliente.id,
            titulo="Cambio de llanta realizado",
            descripcion="Pinchazo en rueda trasera derecha.",
            estado="resuelto",
            latitud=-17.7900, longitud=-63.1900,
            direccion="Calle Libertad",
            categoria="neumaticos", severidad="leve"
        )
        db.add(inc2)
        db.flush()

        sol2 = SolicitudServicio(
            incidente_id=inc2.id, taller_id=taller.id, tecnico_id=tecnico.id,
            estado="completado", notas="Servicio finalizado con éxito. Listo para cobro."
        )
        db.add(sol2)
        db.flush()

        db.commit()
        print("\n" + "="*60)
        print("DEMO V3 LISTA - TODO LIMPIO Y CONFIGURADO")
        print("="*60)
        print("CREDENTIALS (Pass: Password123):")
        print(f" - ADMIN:  {admin.email}")
        print(f" - TALLER: {taller_u.email}")
        print(f" - CLIENTE: {cliente.email}")
    except Exception as e:
        print(f"[ERR] ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_v3()
