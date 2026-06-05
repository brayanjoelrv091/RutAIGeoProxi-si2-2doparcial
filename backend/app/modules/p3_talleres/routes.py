"""
P3 — Rutas de Gestión de Talleres (CU10-CU13).

Endpoints:
    POST   /workshops                      → CU10 Registrar taller
    GET    /workshops                      → Listar mis talleres
    GET    /workshops/all                  → Listar activos (público)
    GET    /workshops/{id}                 → Detalle taller
    POST   /workshops/{id}/technicians     → CU10 Agregar técnico
    GET    /workshops/{id}/technicians     → Listar técnicos
    PATCH  /technicians/{id}/availability  → Toggle disponibilidad
    GET    /workshops/{id}/requests        → CU11 Solicitudes pendientes
    PATCH  /requests/{id}/status           → CU12 Actualizar estado
    GET    /workshops/{id}/history         → CU13 Historial
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.shared.deps import get_current_user, get_db, require_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p3_talleres.schemas import (
    ServiceHistoryOut,
    ServiceRequestOut,
    ServiceStatusUpdate,
    TechnicianAvailabilityUpdate,
    TechnicianCreate,
    TechnicianOut,
    WorkshopCreate,
    WorkshopOut,
)
from app.modules.p3_talleres.services import WorkshopService

router = APIRouter(prefix="/workshops", tags=["P3 · Talleres"])


# ═══════════════════════════════════════════════════════════════════════
# CU10 — Registrar taller y técnicos
# ═══════════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=WorkshopOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU10 · Registrar taller",
)
def register_workshop(
    payload: WorkshopCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.register(db, current.id, payload)


@router.get(
    "",
    response_model=list[WorkshopOut],
    summary="Listar mis talleres",
)
def list_my_workshops(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return WorkshopService.list_by_owner(db, current.id)


@router.get(
    "/active",
    response_model=list[WorkshopOut],
    summary="Listar todos los talleres activos",
)
def list_active_workshops(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return WorkshopService.list_all_active(db, current.tenant_id)





@router.get(
    "/{workshop_id}",
    response_model=WorkshopOut,
    summary="Detalle de un taller",
)
def get_workshop(
    workshop_id: int,
    db: Session = Depends(get_db),
):
    return WorkshopService.get_by_id(db, workshop_id)


@router.post(
    "/{workshop_id}/technicians",
    response_model=TechnicianOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU10 · Agregar técnico al taller",
)
def add_technician(
    workshop_id: int,
    payload: TechnicianCreate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.add_technician(db, workshop_id, current.id, payload)


@router.get(
    "/{workshop_id}/technicians",
    response_model=list[TechnicianOut],
    summary="Listar técnicos del taller",
)
def list_technicians(
    workshop_id: int,
    db: Session = Depends(get_db),
):
    return WorkshopService.list_technicians(db, workshop_id)


# ═══════════════════════════════════════════════════════════════════════
# Disponibilidad de técnicos
# ═══════════════════════════════════════════════════════════════════════

@router.patch(
    "/technicians/{technician_id}/availability",
    response_model=TechnicianOut,
    summary="Toggle disponibilidad de técnico",
)
def update_availability(
    technician_id: int,
    payload: TechnicianAvailabilityUpdate,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.update_technician_availability(
        db, technician_id, current.id, payload.esta_disponible
    )


# ═══════════════════════════════════════════════════════════════════════
# CU11 — Recepción de solicitudes
# ═══════════════════════════════════════════════════════════════════════

@router.get(
    "/{workshop_id}/requests",
    response_model=list[ServiceRequestOut],
    summary="CU11 · Solicitudes pendientes del taller",
)
def list_requests(
    workshop_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.list_pending_requests(db, workshop_id, current.id)


# ═══════════════════════════════════════════════════════════════════════
# CU12 — Actualización de estado
# ═══════════════════════════════════════════════════════════════════════

from fastapi import BackgroundTasks

@router.patch(
    "/requests/{request_id}/status",
    response_model=ServiceRequestOut,
    summary="CU12 · Actualizar estado de solicitud",
)
def update_status(
    request_id: int,
    payload: ServiceStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.update_service_status(db, request_id, current.id, payload, background_tasks)


# ═══════════════════════════════════════════════════════════════════════
# CU13 — Historial de atenciones
# ═══════════════════════════════════════════════════════════════════════

@router.get(
    "/{workshop_id}/history",
    response_model=list[ServiceHistoryOut],
    summary="CU13 · Historial de atenciones del taller",
)
def get_history(
    workshop_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(require_roles("taller", "admin")),
):
    return WorkshopService.get_service_history(db, workshop_id, current.id)
