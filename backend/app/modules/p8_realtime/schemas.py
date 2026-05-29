"""
P8 — Schemas (DTOs) de Conectividad Resiliente y Tiempo Real.

Schemas para:
    - Sincronización offline (CU-21, CU-22, CU-23)
    - Cambios de estado (CU-25)
    - Tracking GPS (CU-26)
    - Mensajes WebSocket (CU-24)
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════


class SyncStatus(str, Enum):
    """Estado de sincronización de un ítem offline."""
    CREATED = "created"
    DUPLICATE = "duplicate"
    ERROR = "error"


class WSEventType(str, Enum):
    """Tipos de eventos WebSocket."""
    STATE_CHANGE = "state_change"
    LOCATION_UPDATE = "location_update"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    ERROR = "error"


# ═══════════════════════════════════════════════════════════════════════
# OFFLINE SYNC (CU-21, CU-22, CU-23)
# ═══════════════════════════════════════════════════════════════════════


class OfflineIncidentPayload(BaseModel):
    """
    CU-21 · Payload de un incidente registrado offline.

    El campo `idempotency_key` es generado por el cliente (UUID v4)
    para garantizar deduplicación en la sincronización.
    """
    idempotency_key: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="UUID v4 generado por el cliente para deduplicación",
    )
    titulo: str = Field(..., min_length=3, max_length=300)
    descripcion: Optional[str] = None
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    direccion: Optional[str] = None
    created_at_local: Optional[datetime] = Field(
        None,
        description="Timestamp local del dispositivo cuando se creó offline",
    )


class OfflineSyncRequest(BaseModel):
    """CU-22 · Batch de incidentes pendientes de sincronización."""
    items: list[OfflineIncidentPayload] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Cola de incidentes offline (máximo 50 por batch)",
    )


class OfflineSyncItemResult(BaseModel):
    """Resultado individual de la sincronización de un ítem offline."""
    idempotency_key: str
    status: SyncStatus
    incident_id: Optional[int] = None
    message: str


class OfflineSyncResponse(BaseModel):
    """CU-22 · Respuesta batch de sincronización."""
    total: int
    created: int
    duplicates: int
    errors: int
    results: list[OfflineSyncItemResult]


# ═══════════════════════════════════════════════════════════════════════
# STATE TRANSITIONS (CU-25)
# ═══════════════════════════════════════════════════════════════════════


class StateChangeRequest(BaseModel):
    """CU-25 · Solicitud de cambio de estado."""
    nuevo_estado: str = Field(
        ...,
        description="Estado destino del incidente",
    )
    notas: Optional[str] = Field(
        None,
        max_length=500,
        description="Notas opcionales del cambio",
    )


class StateChangeResponse(BaseModel):
    """CU-25 · Respuesta tras un cambio de estado exitoso."""
    incidente_id: int
    estado_anterior: str
    estado_nuevo: str
    label: str
    actor_id: int
    actor_rol: str
    transiciones_disponibles: list[str]
    timestamp: datetime


class EventoEstadoOut(BaseModel):
    """Evento de estado para timeline."""
    id: int
    estado_anterior: str
    estado_nuevo: str
    label_anterior: str
    label_nuevo: str
    actor_id: Optional[int]
    actor_rol: Optional[str]
    notas: Optional[str]
    creado_en: datetime

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    """CU-25 · Timeline completo de un incidente."""
    incidente_id: int
    estado_actual: str
    label_actual: str
    es_terminal: bool
    transiciones_disponibles: list[str]
    eventos: list[EventoEstadoOut]


# ═══════════════════════════════════════════════════════════════════════
# TRACKING GPS (CU-26)
# ═══════════════════════════════════════════════════════════════════════


class TrackingGPSPayload(BaseModel):
    """CU-26 · Punto GPS enviado desde el dispositivo móvil."""
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    precision_m: Optional[float] = Field(None, ge=0)
    velocidad_kmh: Optional[float] = Field(None, ge=0)
    heading: Optional[float] = Field(None, ge=0, le=360)
    timestamp: Optional[datetime] = None


class TrackingPointOut(BaseModel):
    """Punto GPS del historial de tracking."""
    id: int
    usuario_id: Optional[int]
    rol: str
    latitud: float
    longitud: float
    precision_m: Optional[float]
    velocidad_kmh: Optional[float]
    heading: Optional[float]
    registrado_en: datetime

    model_config = {"from_attributes": True}


class TrackingHistoryResponse(BaseModel):
    """CU-26 · Historial de posiciones GPS de un incidente."""
    incidente_id: int
    total_puntos: int
    puntos: list[TrackingPointOut]


# ═══════════════════════════════════════════════════════════════════════
# WEBSOCKET MESSAGES (CU-24)
# ═══════════════════════════════════════════════════════════════════════


class WSMessage(BaseModel):
    """Formato estandarizado de mensaje WebSocket."""
    type: WSEventType
    incident_id: Optional[int] = None
    payload: Optional[dict] = None
    timestamp: Optional[datetime] = None
