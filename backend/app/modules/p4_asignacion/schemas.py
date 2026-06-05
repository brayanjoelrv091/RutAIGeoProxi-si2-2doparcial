"""
P4 — Schemas Pydantic para Asignación y Logística.
"""

from datetime import datetime

from pydantic import BaseModel


class AssignmentOut(BaseModel):
    id: int
    incidente_id: int
    taller_id: int
    distancia_km: float
    puntaje: float
    metodo: str
    razonamiento: str | None
    asignado_en: datetime

    model_config = {"from_attributes": True}


class AssignmentDetailOut(AssignmentOut):
    """Incluye datos del taller asignado."""
    nombre_taller: str | None = None
    direccion_taller: str | None = None
    telefono_taller: str | None = None


class CandidateOut(BaseModel):
    """Candidato evaluado durante la asignación (para debug/transparencia)."""
    taller_id: int
    nombre: str
    distancia_km: float
    score_distancia: float
    score_disponibilidad: float
    score_especialidad: float
    puntaje_total: float


class AutoAssignResponse(BaseModel):
    """Respuesta completa de asignación automática."""
    asignacion: AssignmentOut
    candidatos_evaluados: list[CandidateOut] = []
    message: str

class NearbyWorkshopOut(BaseModel):
    taller_id: int
    nombre: str
    direccion: str
    distancia_km: float
    calificacion_promedio: float
    especialidades: list[str] | None

class ManualAssignRequest(BaseModel):
    taller_id: int
    notas: str | None = None
