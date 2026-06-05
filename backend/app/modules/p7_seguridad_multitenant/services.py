"""
P7 — Servicios de Seguridad y Multi-Tenant.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.modules.p7_seguridad_multitenant.models import Tenant, TenantMembership
from app.modules.p7_seguridad_multitenant.schemas import TenantCreate, TenantUpdate, MembershipCreate

class TenantService:
    @staticmethod
    def create_tenant(db: Session, schema: TenantCreate) -> Tenant:
        db_tenant = Tenant(**schema.model_dump())
        try:
            db.add(db_tenant)
            db.commit()
            db.refresh(db_tenant)
            return db_tenant
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El slug del tenant ya existe",
            )

    @staticmethod
    def get_tenants(db: Session, skip: int = 0, limit: int = 100) -> list[Tenant]:
        return db.query(Tenant).offset(skip).limit(limit).all()

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: int) -> Tenant:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant no encontrado",
            )
        return tenant

    @staticmethod
    def update_tenant(db: Session, tenant_id: int, schema: TenantUpdate) -> Tenant:
        tenant = TenantService.get_tenant_by_id(db, tenant_id)
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tenant, key, value)
        try:
            db.commit()
            db.refresh(tenant)
            return tenant
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El slug ya existe o hay un conflicto de datos",
            )

    @staticmethod
    def add_member(db: Session, tenant_id: int, schema: MembershipCreate) -> TenantMembership:
        # Validar que no exista ya
        existing = db.query(TenantMembership).filter(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.usuario_id == schema.usuario_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya es miembro de este tenant",
            )
            
        membership = TenantMembership(
            tenant_id=tenant_id,
            usuario_id=schema.usuario_id,
            rol_en_tenant=schema.rol_en_tenant
        )
        try:
            db.add(membership)
            db.commit()
            db.refresh(membership)
            
            # Asignar el tenant_id actual al usuario
            from app.modules.p1_usuarios.models import Usuario
            usuario = db.query(Usuario).filter(Usuario.id == schema.usuario_id).first()
            if usuario:
                usuario.tenant_id = tenant_id
                db.commit()
                
            return membership
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al agregar miembro. ¿Usuario existe?",
            )

    @staticmethod
    def remove_member(db: Session, tenant_id: int, usuario_id: int):
        membership = db.query(TenantMembership).filter(
            TenantMembership.tenant_id == tenant_id,
            TenantMembership.usuario_id == usuario_id
        ).first()
        
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Miembro no encontrado",
            )
            
        db.delete(membership)
        
        # Remover tenant_id del usuario si lo tenía
        from app.modules.p1_usuarios.models import Usuario
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if usuario and usuario.tenant_id == tenant_id:
            usuario.tenant_id = None
            
        db.commit()

    @staticmethod
    def list_members(db: Session, tenant_id: int) -> list[TenantMembership]:
        return db.query(TenantMembership).filter(TenantMembership.tenant_id == tenant_id).all()


class TenantFilterService:
    """Lógica para aplicar row-level security / filtros automáticos."""
    
    @staticmethod
    def apply_tenant_filter(query, model, tenant_id: int | None):
        """Filtra una query de SQLAlchemy para retornar solo registros del tenant_id especificado."""
        if tenant_id is None:
            # Si no hay tenant_id, podríamos restringir a 0 resultados o dejar que un superadmin vea todo.
            # Por seguridad, si tenant_id es None (usuario no asignado a org), no debería ver datos de otras orgs.
            # Vamos a retornar los que tienen tenant_id IS NULL.
            return query.filter(model.tenant_id.is_(None))
        
        return query.filter(model.tenant_id == tenant_id)
