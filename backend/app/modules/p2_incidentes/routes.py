"""
P2 — Rutas de Gestión de Incidentes.

Endpoints:
    POST   /incidents           → CU7  Reportar incidente
    GET    /incidents           → Listar mis incidentes
    GET    /incidents/all       → Listar todos (admin)
    GET    /incidents/{id}      → CU9  Ficha técnica
    POST   /incidents/{id}/classify → CU8 Re-clasificar
"""

from fastapi import APIRouter, Depends, File, Form, UploadFile, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.shared.deps import get_current_user, get_db, require_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p2_incidentes.schemas import (
    ClassificationOut,
    IncidentCreate,
    IncidentDetailOut,
    IncidentOut,
)
from app.modules.p2_incidentes.services import IncidentService

router = APIRouter(prefix="/incidents", tags=["P2 · Incidentes"])


@router.post(
    "",
    response_model=IncidentDetailOut,
    status_code=status.HTTP_201_CREATED,
    summary="CU7 · Reportar incidente con fotos/audio/GPS",
)
async def create_incident(
    titulo: str = Form(..., min_length=3, max_length=300),
    latitud: float = Form(...),
    longitud: float = Form(...),
    descripcion: str | None = Form(default=None),
    direccion: str | None = Form(default=None),
    fotos: list[UploadFile] = File(default=[]),
    audio: UploadFile | None = File(default=None),
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    payload = IncidentCreate(
        titulo=titulo,
        descripcion=descripcion,
        latitud=latitud,
        longitud=longitud,
        direccion=direccion,
    )
    incidente = await IncidentService.create(
        db=db,
        user_id=current.id,
        payload=payload,
        fotos=fotos if fotos else None,
        audio=audio,
        background_tasks=background_tasks
    )
    # Reload con relaciones
    return IncidentService.get_detail(db, incidente.id)


@router.get(
    "",
    response_model=list[IncidentOut],
    summary="Listar mis incidentes",
)
def list_my_incidents(
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    return IncidentService.list_by_user(db, current.id)


@router.get(
    "/all",
    response_model=list[IncidentOut],
    summary="Listar todos los incidentes (admin)",
)
def list_all_incidents(
    db: Session = Depends(get_db),
    _current: Usuario = Depends(require_roles("admin")),
):
    return IncidentService.list_all(db)


@router.get(
    "/{incident_id}",
    response_model=IncidentDetailOut,
    summary="CU9 · Ficha técnica del incidente",
)
def get_incident_detail(
    incident_id: int,
    db: Session = Depends(get_db),
    current: Usuario = Depends(get_current_user),
):
    # Si es admin, no pasamos user_id para saltar la validación de propiedad
    user_id_to_check = current.id if current.rol != "admin" else None
    return IncidentService.get_detail(db, incident_id, user_id_to_check)


@router.post(
    "/{incident_id}/classify",
    response_model=ClassificationOut,
    summary="CU8 · Re-clasificar incidente (IA)",
)
async def reclassify_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(require_roles("admin")),
):
    return await IncidentService.reclassify(db, incident_id)
