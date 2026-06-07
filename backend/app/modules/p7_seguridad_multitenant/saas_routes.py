from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.shared.deps import get_db, require_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p7_seguridad_multitenant.models import Tenant

router = APIRouter(tags=["P7 · Gestión SaaS (SuperAdmin)"])

class TenantStatusUpdate(BaseModel):
    esta_activo: bool

class TenantOut(BaseModel):
    id: int
    nombre: str
    slug: str
    esta_activo: bool
    plan: str
    creado_en: datetime
    
    class Config:
        from_attributes = True

def require_superadmin(current: Usuario = Depends(require_roles("admin"))):
    """Verifica que sea un admin GLOBAL (sin tenant)."""
    if current.tenant_id is not None:
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requieren privilegios de SuperAdmin del sistema.")
    return current

@router.get("/tenants", response_model=List[TenantOut], summary="Listar todos los tenants (Solo SuperAdmin)")
def list_all_tenants(
    db: Session = Depends(get_db),
    _current: Usuario = Depends(require_superadmin)
):
    """Obtiene la lista de todas las suscripciones (empresas) registradas en el sistema."""
    return db.query(Tenant).order_by(Tenant.creado_en.desc()).all()

@router.patch("/tenants/{tenant_id}/status", response_model=TenantOut, summary="Activar o suspender un tenant (Solo SuperAdmin)")
def update_tenant_status(
    tenant_id: int,
    payload: TenantStatusUpdate,
    db: Session = Depends(get_db),
    _current: Usuario = Depends(require_superadmin)
):
    """Permite al SuperAdmin suspender o reactivar una empresa por falta de pago o incumplimiento."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    
    tenant.esta_activo = payload.esta_activo
    db.commit()
    db.refresh(tenant)
    return tenant
