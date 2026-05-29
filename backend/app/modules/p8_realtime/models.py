"""
P8 — Modelos de Conectividad Resiliente y Tiempo Real.

Tablas:
    - ``evento_estados``   → CU-25  Historial de transiciones de estado
    - ``tracking_gps``     → CU-26  Coordenadas GPS en vivo
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.shared.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class EventoEstado(Base):
    """
    CU-25 · Registro inmutable de cada transición de estado de un incidente.

    Provee trazabilidad completa del ciclo de vida:
    quién cambió el estado, cuándo, y desde/hacia qué estado.
    """

    __tablename__ = "evento_estados"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(
        Integer,
        ForeignKey("incidentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estado_anterior = Column(String(30), nullable=False)
    estado_nuevo = Column(String(30), nullable=False)
    actor_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_rol = Column(String(20), nullable=True)  # admin | taller | cliente | sistema
    notas = Column(Text, nullable=True)
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    # ── Relaciones ──
    incidente = relationship("Incidente", backref="eventos_estado")
    actor = relationship("Usuario", backref="eventos_realizados")


class TrackingGPS(Base):
    """
    CU-26 · Punto de tracking GPS en tiempo real.

    Registra la posición instantánea de un técnico o cliente
    durante la atención de una emergencia vehicular.
    """

    __tablename__ = "tracking_gps"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(
        Integer,
        ForeignKey("incidentes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    rol = Column(String(20), nullable=False, default="tecnico")  # tecnico | cliente
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    precision_m = Column(Float, nullable=True)       # Precisión GPS en metros
    velocidad_kmh = Column(Float, nullable=True)     # Velocidad instantánea
    heading = Column(Float, nullable=True)           # Dirección en grados (0-360)
    registrado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_utc_now,
    )

    # ── Relaciones ──
    incidente = relationship("Incidente", backref="tracking_points")
    usuario = relationship("Usuario", backref="tracking_enviados")
