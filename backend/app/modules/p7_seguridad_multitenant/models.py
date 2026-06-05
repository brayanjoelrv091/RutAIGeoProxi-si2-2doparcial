"""
P7 — Modelos de Seguridad y Multi-Tenant (CU-28, CU-29).

Tablas:
    - ``tenants``
    - ``tenant_memberships``
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.shared.database import Base


class Tenant(Base):
    """CU29 · Organización / Empresa (Ej: Franquicia de talleres)."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    esta_activo = Column(Boolean, default=True, nullable=False)
    plan = Column(String(50), default="basico", nullable=False)
    creado_en = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relaciones ──
    miembros = relationship(
        "TenantMembership", back_populates="tenant", cascade="all, delete-orphan"
    )
    # Incidentes, Usuarios y Talleres relacionados usan string refs


class TenantMembership(Base):
    """CU29 · Relación M:N entre Usuario y Tenant (Roles dentro de la org)."""

    __tablename__ = "tenant_memberships"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rol_en_tenant = Column(String(50), nullable=False, default="miembro")  # owner | admin | miembro

    # ── Relaciones ──
    tenant = relationship("Tenant", back_populates="miembros")
    # 'usuario' no se define aquí como back_populates para evitar circular dependency, 
    # se usará ref simple o query directa.
