"""
P4 — Rutas de Asignación y Logística (CU14 - CU15).

Endpoints:
    POST /assignments/auto/{incident_id}  → CU14 Asignación automática
    GET  /assignments/{incident_id}       → Ver asignación
    WS   /ws/track/{incident_id}         → CU15 Geoproximidad avanzada
"""

from fastapi import APIRouter, Depends, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.shared.deps import get_current_user, get_db, require_roles, require_operational_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p4_asignacion.schemas import (
    AssignmentOut,
    AutoAssignResponse,
    CandidateOut,
    NearbyWorkshopOut,
    ManualAssignRequest
)
from app.modules.p4_asignacion.services import AssignmentService
from app.shared.websocket_manager import manager

router = APIRouter(prefix="/assignments", tags=["P4 · Asignación y Logística"])

admin_dep = require_operational_roles("admin")


from fastapi import BackgroundTasks

@router.post(
    "/auto/{incident_id}",
    response_model=AutoAssignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="CU14 · Asignación automática del taller más adecuado",
)
def auto_assign(
    incident_id: int,
    background_tasks: BackgroundTasks,
    max_radius_km: float = Query(default=50.0, ge=1, le=500),
    db: Session = Depends(get_db),
    _current: Usuario = Depends(admin_dep),
):
    asignacion, candidates = AssignmentService.auto_assign(
        db, incident_id, max_radius_km, background_tasks
    )
    return AutoAssignResponse(
        asignacion=AssignmentOut.model_validate(asignacion),
        candidatos_evaluados=[
            CandidateOut(
                taller_id=c.taller_id,
                nombre=c.nombre,
                distancia_km=c.distancia_km,
                score_distancia=round(c.score_distancia, 4),
                score_disponibilidad=round(c.score_disponibilidad, 4),
                score_especialidad=round(c.score_especialidad, 4),
                puntaje_total=c.puntaje_total,
            )
            for c in candidates
        ],
        message=f"Taller '{candidates[0].nombre}' asignado ({candidates[0].distancia_km} km)",
    )


@router.get(
    "/{incident_id}",
    response_model=AssignmentOut,
    summary="Ver asignación de un incidente",
)
def get_assignment(
    incident_id: int,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    return AssignmentService.get_assignment(db, incident_id)


@router.websocket("/ws/track/{incident_id}")
async def track_incident(websocket: WebSocket, incident_id: int):
    """
    CU15 · Seguimiento en tiempo real de la ubicación del técnico/cliente.
    """
    await manager.connect(websocket, str(incident_id))
    try:
        while True:
            # Recibe la ubicación { "lat": ..., "lng": ..., "role": "tecnico"|"cliente" }
            data = await websocket.receive_json()
            # Retransmite a todos los interesados en este incidente
            await manager.send_personal_message(
                {
                    "type": "location_update",
                    "incident_id": incident_id,
                    "lat": data.get("lat"),
                    "lng": data.get("lng"),
                    "role": data.get("role"),
                    "timestamp": data.get("timestamp"),
                },
                str(incident_id),
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(incident_id))

@router.get(
    "/workshops/nearby/{incident_id}",
    response_model=list[NearbyWorkshopOut],
    summary="CU31 · Listar talleres cercanos al incidente"
)
def list_nearby_workshops(
    incident_id: int,
    max_radius_km: float = Query(default=50.0, ge=1, le=500),
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    return AssignmentService.list_nearby_workshops(db, incident_id, max_radius_km)


@router.post(
    "/manual/{incident_id}",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU31 · Asignación manual de taller"
)
def manual_assign(
    incident_id: int,
    request: ManualAssignRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(get_current_user),
):
    return AssignmentService.manual_assign(db, incident_id, request.taller_id, request.notas, background_tasks)
