"""
RutAIGeoProxi — API Backend (Monolito Modular).

Entry point que registra todos los módulos y configura el servidor.

Arquitectura:
    P1 · Usuarios y Seguridad     (CU1-CU6)   ✅ Implementado
    P2 · Gestión de Incidentes     (CU7-CU9)   ✅ Implementado
    P3 · Gestión de Talleres       (CU10-CU13)  ✅ Implementado
    P4 · Asignación y Logística    (CU14-CU15)  ✅ Implementado
    P5 · Pagos y Notificaciones    (CU16-CU18)  ✅ Implementado
    P6 · Reportes                  (CU19-CU20)  ✅ Implementado
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.shared.config import settings
from app.shared.database import Base, SessionLocal, engine
from app.shared.security import get_password_hash

# ── Importar modelos de TODOS los módulos para que SQLAlchemy los registre ──
from app.modules.p1_usuarios.models import (  # noqa: F401
    TokenRecuperacion,
    TokenRevocado,
    Usuario,
    Vehiculo,
)
from app.modules.p2_incidentes.models import (  # noqa: F401
    ClasificacionIncidente,
    Incidente,
    IncidenteMedia,
)
from app.modules.p3_talleres.models import (  # noqa: F401
    SolicitudServicio,
    Taller,
    Tecnico,
)
from app.modules.p4_asignacion.models import Asignacion  # noqa: F401
from app.modules.p5_pagos.models import Pago, Notificacion  # noqa: F401
from app.modules.p6_reportes.models import ReporteGenerado  # noqa: F401

# ── Importar routers de módulos ──
from app.modules.p1_usuarios.routes import admin_router, auth_router, profile_router
from app.modules.p2_incidentes.routes import router as incidents_router
from app.modules.p3_talleres.routes import router as workshops_router
from app.modules.p4_asignacion.routes import router as assignments_router
from app.modules.p5_pagos.routes import router as payments_router
from app.modules.p6_reportes.routes import router as reports_router
from app.modules.p6_auditoria.routes import router as audit_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# LIFESPAN (startup / shutdown)
# ═══════════════════════════════════════════════════════════════════════


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Crea tablas y seed del admin al iniciar."""
    logger.info("🚀 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tablas creadas/verificadas")

    # Seed del administrador
    if settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
        db = SessionLocal()
        try:
            if (
                not db.query(Usuario)
                .filter(Usuario.email == settings.ADMIN_EMAIL)
                .first()
            ):
                db.add(
                    Usuario(
                        nombre="Administrador",
                        email=settings.ADMIN_EMAIL,
                        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                        rol="admin",
                        esta_activo=True,
                    )
                )
                db.commit()
                logger.info(f"👤 Admin seed creado: {settings.ADMIN_EMAIL}")
        finally:
            db.close()

    # Crear directorio de uploads si no existe
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    yield
    logger.info("🛑 Servidor detenido")


# ═══════════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="RutAIGeoProxi API",
    description="Red de Asistencia Técnica Vehicular Inteligente — Monolito Modular",
    version="2.1.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Servir archivos estáticos (uploads locales) ──
if settings.UPLOAD_DIR.exists():
    app.mount(
        "/uploads", StaticFiles(directory=str(settings.UPLOAD_DIR)), name="uploads"
    )

# ── Registrar routers de módulos ──
# P1: Usuarios y Seguridad
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(profile_router)
# P2: Incidentes
app.include_router(incidents_router)
# P3: Talleres
app.include_router(workshops_router)
# P4: Asignación
app.include_router(assignments_router)
# P5: Pagos y Notificaciones
app.include_router(payments_router)
# P6: Reportes y Auditoría
app.include_router(reports_router)
app.include_router(audit_router)


# ── Root endpoint ──
@app.get("/", tags=["Sistema"])
def root():
    """Mapa de la API por ciclo y caso de uso."""
    return {
        "api": "RutAIGeoProxi",
        "version": "2.1.0",
        "arquitectura": "Monolito Modular",
        "modulos": {
            "P1_usuarios_seguridad": {
                "estado": "✅ Implementado",
                "CU1_inicio_sesion": "POST /auth/login",
                "CU2_cierre_sesion": "POST /auth/logout",
                "CU3_registro": "POST /auth/register",
                "CU4_recuperar_password": "POST /auth/forgot-password + /auth/reset-password",
                "CU5_roles_permisos": "GET/POST /admin/users, PATCH /admin/users/{id}/role|permissions",
                "CU6_usuario_vehiculo": "GET/PATCH /me, GET/POST/PATCH/DELETE /me/vehicles",
            },
            "P2_incidentes": {
                "estado": "✅ Implementado",
                "CU7_reportar_incidente": "POST /incidents (multipart: fotos+audio+GPS)",
                "CU8_clasificacion_ia": "POST /incidents/{id}/classify (Groq-LLM+Roboflow+Whisper)",
                "CU9_ficha_incidente": "GET /incidents/{id}",
            },
            "P3_talleres": {
                "estado": "✅ Implementado",
                "CU10_registrar_taller": "POST /workshops + POST /workshops/{id}/technicians",
                "CU11_solicitudes": "GET /workshops/{id}/requests",
                "CU12_actualizar_estado": "PATCH /workshops/requests/{id}/status",
                "CU13_historial": "GET /workshops/{id}/history",
            },
            "P4_asignacion": {
                "estado": "✅ Implementado",
                "CU14_asignacion_automatica": "POST /assignments/auto/{incident_id}",
                "CU15_tracking_ws": "WS /assignments/ws/track/{incident_id}",
            },
            "P5_pagos_notificaciones": {
                "estado": "✅ Implementado",
                "CU18_procesar_pago_simulado": "POST /payments/process",
                "CU16_CU17_notificaciones_ws": "WS /payments/ws/notifications/{user_id}",
            },
            "P6_reportes": {
                "estado": "✅ Implementado",
                "CU19_generacion_datos": "Backend logic",
                "CU20_exportar_pdf_excel": "GET /reports/incidents/pdf | excel",
            },
        },
        "docs": "/docs",
    }
