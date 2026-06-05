"""
P5 — Modelos de Pagos y Notificaciones.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from app.shared.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class Pago(Base):
    """
    CU18 · Registro de transacciones (Simulado).
    """

    __tablename__ = "pagos"

    id = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id"), nullable=False)
    monto = Column(Float, nullable=False)
    comision_plataforma = Column(Float, default=0.0)  # 10% para la empresa
    moneda = Column(String(10), default="USD")
    estado = Column(String(30), default="pendiente")  # pendiente | completado | fallido
    metodo_pago = Column(String(50))  # tarjeta | transferencia | efectivo
    proveedor = Column(String(50), default="stripe")
    transaccion_id = Column(String(100), unique=True)  # ID externo simulado o real
    gateway_response = Column(Text, nullable=True) # JSON raw de la respuesta del proveedor
    creado_at = Column(DateTime, default=_utc_now)


class Notificacion(Base):
    """
    CU16 · Historial de notificaciones enviadas.
    """

    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    leido = Column(Boolean, default=False)  # False: No leido, True: Leido
    tipo = Column(String(50))  # push | email | sistema
    creado_at = Column(DateTime, default=_utc_now)
