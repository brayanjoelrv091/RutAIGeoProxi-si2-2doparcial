"""
P7 — Schemas Pydantic para Seguridad y Multi-Tenant.
"""

from datetime import datetime
from pydantic import BaseModel, Field

class TenantBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=100)
    esta_activo: bool = True
    plan: str = "basico"

class TenantCreate(TenantBase):
    pass

class TenantUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=200)
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    esta_activo: bool | None = None
    plan: str | None = None

class TenantOut(TenantBase):
    id: int
    creado_en: datetime

    model_config = {"from_attributes": True}

class MembershipCreate(BaseModel):
    usuario_id: int
    rol_en_tenant: str = "miembro"

class MembershipOut(BaseModel):
    id: int
    usuario_id: int
    tenant_id: int
    rol_en_tenant: str

    model_config = {"from_attributes": True}
