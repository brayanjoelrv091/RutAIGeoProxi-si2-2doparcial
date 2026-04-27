from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.shared.database import get_db
from app.shared.deps import require_roles
from app.modules.p1_usuarios.models import Usuario
from app.modules.p6_auditoria.services import AuditService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/admin/audit", tags=["P6 · Auditoría"])

class BitacoraOut(BaseModel):
    id: int
    usuario_id: int | None
    rol: str | None
    accion: str
    ip: str | None = None
    creado_en: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[BitacoraOut], summary="Listar bitácora de auditoría (Solo Admin)")
def list_audit_logs(
    db: Session = Depends(get_db),
    _current: Usuario = Depends(require_roles("admin"))
):
    """
    Retorna todos los eventos registrados en la bitácora.
    Solo accesible por usuarios con rol 'admin'.
    """
    from app.modules.p6_auditoria.models import Bitacora
    return db.query(Bitacora).order_by(Bitacora.creado_en.desc()).all()
