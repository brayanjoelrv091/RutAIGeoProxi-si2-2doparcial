"""
P3 — Capa de servicios de Talleres (CU10, CU11, CU12, CU13).
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.modules.p2_incidentes.models import Incidente
from app.modules.p3_talleres.models import SolicitudServicio, Taller, Tecnico
from app.modules.p3_talleres.schemas import (
    TRANSICIONES_VALIDAS,
    ServiceStatusUpdate,
    TechnicianCreate,
    WorkshopCreate,
)


class WorkshopService:
    """Servicio de gestión de talleres y técnicos."""

    # ── CU10: Registrar taller ─────────────────────────────────────

    @staticmethod
    def register(db: Session, user_id: int, payload: WorkshopCreate) -> Taller:
        """CU10 — Registrar un nuevo taller."""
        # Obtener tenant_id del usuario propietario
        from app.modules.p1_usuarios.models import Usuario
        user = db.query(Usuario).filter(Usuario.id == user_id).first()
        tenant_id = user.tenant_id if user else None

        taller = Taller(
            usuario_propietario_id=user_id,
            tenant_id=tenant_id,
            nombre=payload.nombre,
            direccion=payload.direccion,
            latitud=payload.latitud,
            longitud=payload.longitud,
            telefono=payload.telefono,
            email=payload.email,
            especialidades=payload.especialidades,
        )
        db.add(taller)
        db.commit()
        db.refresh(taller)
        return taller

    @staticmethod
    def get_by_id(db: Session, workshop_id: int) -> Taller:
        taller = db.query(Taller).filter(Taller.id == workshop_id).first()
        if not taller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taller no encontrado",
            )
        return taller

    @staticmethod
    def list_by_owner(db: Session, user_id: int) -> list[Taller]:
        return (
            db.query(Taller)
            .filter(Taller.usuario_propietario_id == user_id)
            .order_by(Taller.id)
            .all()
        )

    @staticmethod
    def list_all_active(db: Session, tenant_id: int | None = None) -> list[Taller]:
        from app.modules.p7_seguridad_multitenant.services import TenantFilterService
        query = db.query(Taller).filter(Taller.esta_activo.is_(True))
        if tenant_id is not None:
            query = TenantFilterService.apply_tenant_filter(query, Taller, tenant_id)
        return query.order_by(Taller.nombre).all()

    # ── CU10: Registrar técnicos ───────────────────────────────────

    @staticmethod
    def add_technician(
        db: Session, workshop_id: int, owner_id: int, payload: TechnicianCreate
    ) -> Tecnico:
        """CU10 — Agregar técnico a un taller."""
        taller = db.query(Taller).filter(Taller.id == workshop_id).first()
        if not taller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taller no encontrado",
            )
        if taller.usuario_propietario_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el propietario del taller puede agregar técnicos",
            )
        tecnico = Tecnico(
            taller_id=workshop_id,
            nombre=payload.nombre,
            telefono=payload.telefono,
            especialidad=payload.especialidad,
            latitud=payload.latitud,
            longitud=payload.longitud,
        )
        db.add(tecnico)
        db.commit()
        db.refresh(tecnico)
        return tecnico

    @staticmethod
    def list_technicians(db: Session, workshop_id: int) -> list[Tecnico]:
        return (
            db.query(Tecnico)
            .filter(Tecnico.taller_id == workshop_id)
            .order_by(Tecnico.id)
            .all()
        )

    @staticmethod
    def update_technician_availability(
        db: Session, technician_id: int, owner_id: int, available: bool
    ) -> Tecnico:
        tecnico = (
            db.query(Tecnico)
            .join(Taller, Tecnico.taller_id == Taller.id)
            .filter(
                Tecnico.id == technician_id,
                Taller.usuario_propietario_id == owner_id,
            )
            .first()
        )
        if not tecnico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Técnico no encontrado o sin permisos",
            )
        tecnico.esta_disponible = available
        db.commit()
        db.refresh(tecnico)
        return tecnico

    # ── CU11: Recepción de solicitudes ─────────────────────────────

    @staticmethod
    def list_pending_requests(
        db: Session, workshop_id: int, owner_id: int
    ) -> list[SolicitudServicio]:
        """CU11 — Listar solicitudes pendientes de un taller."""
        taller = db.query(Taller).filter(Taller.id == workshop_id).first()
        if not taller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taller no encontrado",
            )
        if taller.usuario_propietario_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permisos para ver solicitudes de este taller",
            )
        solicitudes = (
            db.query(SolicitudServicio)
            .options(
                joinedload(SolicitudServicio.incidente).joinedload(Incidente.clasificacion)
            )
            .filter(
                SolicitudServicio.taller_id == workshop_id,
                SolicitudServicio.estado.in_(["pendiente", "proceso"]),
            )
            .order_by(SolicitudServicio.creado_en.desc())
            .all()
        )

        result = []
        for s in solicitudes:
            item = {
                "id": s.id,
                "incidente_id": s.incidente_id,
                "taller_id": s.taller_id,
                "tecnico_id": s.tecnico_id,
                "estado": s.estado,
                "notas": s.notas,
                "creado_en": s.creado_en,
                "actualizado_en": s.actualizado_en,
                "titulo_incidente": s.incidente.titulo if s.incidente else None,
                "categoria_incidente": s.incidente.categoria if s.incidente else None,
                "severidad_incidente": s.incidente.severidad if s.incidente else None,
                "resumen_ia": s.incidente.clasificacion.razonamiento if s.incidente and s.incidente.clasificacion else None,
            }
            result.append(item)
        return result

    # ── CU12: Actualización de estado ──────────────────────────────

    from fastapi import BackgroundTasks
    @staticmethod
    def update_service_status(
        db: Session,
        request_id: int,
        owner_id: int,
        payload: ServiceStatusUpdate,
        background_tasks: BackgroundTasks = None,
    ) -> SolicitudServicio:
        """
        CU12 — Actualizar estado de solicitud con validación de transiciones.
        Transiciones válidas:
            pendiente → proceso | cancelado
            proceso   → atendido | cancelado
        """
        solicitud = (
            db.query(SolicitudServicio)
            .join(Taller, SolicitudServicio.taller_id == Taller.id)
            .filter(
                SolicitudServicio.id == request_id,
                Taller.usuario_propietario_id == owner_id,
            )
            .first()
        )
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Solicitud no encontrada o sin permisos",
            )

        # Validar transición de estado
        allowed = TRANSICIONES_VALIDAS.get(solicitud.estado, set())
        if payload.estado not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Transición inválida: '{solicitud.estado}' → '{payload.estado}'. "
                    f"Permitidas: {', '.join(sorted(allowed)) if allowed else 'ninguna (estado final)'}"
                ),
            )

        solicitud.estado = payload.estado
        if payload.notas:
            solicitud.notas = payload.notas
        if payload.tecnico_id:
            solicitud.tecnico_id = payload.tecnico_id

        # Sincronizar estado del incidente
        if payload.estado == "proceso":
            incidente = db.query(Incidente).filter(
                Incidente.id == solicitud.incidente_id
            ).first()
            if incidente:
                incidente.estado = "en_proceso"
        elif payload.estado == "atendido":
            incidente = db.query(Incidente).filter(
                Incidente.id == solicitud.incidente_id
            ).first()
            if incidente:
                incidente.estado = "resuelto"

        db.commit()
        db.refresh(solicitud)

        # CU16 - Notificar al cliente dueño del incidente
        from app.modules.p5_pagos.services import NotificationService
        incidente = db.query(Incidente).filter(Incidente.id == solicitud.incidente_id).first()
        if incidente and background_tasks:
            background_tasks.add_task(
                NotificationService.send_push_notification,
                db=db,
                user_id=incidente.usuario_id,
                titulo="Actualización de Servicio",
                mensaje=f"Tu incidente ha cambiado al estado: {payload.estado.upper()}"
            )

        return solicitud

    # ── CU13: Historial de atenciones ──────────────────────────────

    @staticmethod
    def get_service_history(
        db: Session, workshop_id: int, owner_id: int
    ) -> list[dict]:
        """CU13 — Historial de todas las atenciones del taller."""
        taller = db.query(Taller).filter(Taller.id == workshop_id).first()
        if not taller:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Taller no encontrado",
            )
        if taller.usuario_propietario_id != owner_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permisos para ver historial de este taller",
            )

        solicitudes = (
            db.query(SolicitudServicio)
            .options(
                joinedload(SolicitudServicio.incidente).joinedload(Incidente.clasificacion)
            )
            .filter(SolicitudServicio.taller_id == workshop_id)
            .order_by(SolicitudServicio.creado_en.desc())
            .all()
        )

        result = []
        for s in solicitudes:
            item = {
                "id": s.id,
                "incidente_id": s.incidente_id,
                "taller_id": s.taller_id,
                "tecnico_id": s.tecnico_id,
                "estado": s.estado,
                "notas": s.notas,
                "creado_en": s.creado_en,
                "actualizado_en": s.actualizado_en,
                "titulo_incidente": s.incidente.titulo if s.incidente else None,
                "categoria_incidente": s.incidente.categoria if s.incidente else None,
                "severidad_incidente": s.incidente.severidad if s.incidente else None,
                "resumen_ia": s.incidente.clasificacion.razonamiento if s.incidente and s.incidente.clasificacion else None,
            }
            result.append(item)
        return result
