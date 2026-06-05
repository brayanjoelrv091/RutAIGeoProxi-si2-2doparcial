"""
P9 — Rutas de Analítica y Operaciones.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.shared.deps import get_current_user, get_db, get_current_tenant_id, require_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p9_analitica.schemas import (
    DashboardKPIs,
    CotizacionOut,
    TiempoEstimadoOut
)
from app.modules.p9_analitica.services import DashboardService, CotizacionService, EstimacionService

router = APIRouter(prefix="/analytics", tags=["P9 · Analítica Operacional y Cotizaciones"])

# ── Dashboard KPIs ──

@router.get("/dashboard", response_model=DashboardKPIs, summary="CU27 · Dashboard de KPIs")
def get_dashboard(
    tenant_id: int | None = None, # Opcional: superadmin puede consultar un tenant específico
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene métricas operacionales del tenant actual."""
    # Si es admin y pide un tenant_id específico, lo usamos. Sino usamos el suyo.
    target_tenant = tenant_id if (current_user.rol == "admin" and tenant_id) else current_user.tenant_id
    return DashboardService.get_kpis(db, target_tenant)


# ── Estimaciones y Cotizaciones ──

@router.get("/estimate/{incident_id}", response_model=TiempoEstimadoOut, summary="CU32 · Calcular tiempo estimado")
def get_estimacion(
    incident_id: int,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    """Calcula el tiempo estimado de reparación basado en la severidad y categoría del incidente."""
    return EstimacionService.calcular_tiempo_estimado(db, incident_id)


@router.post("/quotations/{incident_id}", response_model=CotizacionOut, status_code=status.HTTP_201_CREATED, summary="CU30 · Generar Cotización")
def generar_cotizacion(
    incident_id: int,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    """Genera una cotización detallada basándose en el análisis de IA del incidente."""
    return CotizacionService.generar_cotizacion_desde_ia(db, incident_id)


@router.get("/quotations/{cotizacion_id}", response_model=CotizacionOut, summary="Ver detalle de Cotización")
def get_cotizacion(
    cotizacion_id: int,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    """Obtiene los detalles y desgloses de una cotización."""
    return CotizacionService.get_cotizacion(db, cotizacion_id)
