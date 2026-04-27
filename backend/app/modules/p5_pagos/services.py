import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modules.p1_usuarios.models import Usuario
from app.modules.p2_incidentes.models import Incidente
from app.modules.p3_talleres.models import SolicitudServicio, Taller
from app.modules.p5_pagos.models import Notificacion, Pago
from app.modules.p5_pagos.schemas import PagoCreate
from app.shared.websocket_manager import manager


class PaymentService:
    @staticmethod
    async def process_payment(
        db: Session,
        pago_in: PagoCreate,
        current_user: Usuario,
    ) -> Pago:
        """
        CU18 · Simula el procesamiento de un pago.

        Reglas:
            - El incidente debe existir.
            - Un cliente solo puede pagar sus propios incidentes.
            - Un taller no puede procesar pagos directamente.
            - Se evita duplicar pagos completados para el mismo incidente.
        """
        incidente = (
            db.query(Incidente)
            .filter(Incidente.id == pago_in.incidente_id)
            .first()
        )
        if not incidente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidente no encontrado",
            )

        if current_user.rol == "cliente" and incidente.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede pagar incidentes de otro usuario",
            )

        if current_user.rol not in {"admin", "cliente"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un cliente o admin puede procesar pagos",
            )

        pago_existente = (
            db.query(Pago)
            .filter(
                Pago.incidente_id == pago_in.incidente_id,
                Pago.estado == "completado",
            )
            .first()
        )
        if pago_existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este incidente ya tiene un pago completado",
            )

        transaccion_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
        monto_total = pago_in.monto
        comision = monto_total * 0.10

        nuevo_pago = Pago(
            incidente_id=pago_in.incidente_id,
            monto=monto_total,
            comision_plataforma=comision,
            moneda=pago_in.moneda,
            metodo_pago=pago_in.metodo_pago,
            estado="completado",
            transaccion_id=transaccion_id,
        )
        db.add(nuevo_pago)

        from app.modules.p6_auditoria.services import AuditService

        AuditService.log(
            db,
            usuario_id=current_user.id,
            rol=current_user.rol,
            accion=(
                f"Pago procesado para incidente #{pago_in.incidente_id}. "
                f"Comision 10%: {comision:.2f} {pago_in.moneda}"
            ),
        )

        recipient_ids = {incidente.usuario_id}
        workshop_owner_ids = (
            db.query(Taller.usuario_propietario_id)
            .join(SolicitudServicio, SolicitudServicio.taller_id == Taller.id)
            .filter(SolicitudServicio.incidente_id == pago_in.incidente_id)
            .distinct()
            .all()
        )
        recipient_ids.update(owner_id for (owner_id,) in workshop_owner_ids)

        message = (
            f"💰 Pago exitoso: {monto_total:.2f} {pago_in.moneda}. "
            f"Comisión App (10%): -{comision:.2f} {pago_in.moneda}. "
            f"Ganancia Taller: {monto_total - comision:.2f} {pago_in.moneda}."
        )
        for user_id in sorted(recipient_ids):
            db.add(
                Notificacion(
                    usuario_id=user_id,
                    titulo="Pago aprobado",
                    mensaje=message,
                    tipo="push",
                )
            )

        db.commit()
        db.refresh(nuevo_pago)

        payload = {
            "type": "payment_approved",
            "incidente_id": nuevo_pago.incidente_id,
            "monto": nuevo_pago.monto,
            "moneda": nuevo_pago.moneda,
            "transaccion_id": transaccion_id,
            "title": "Pago aprobado",
            "message": message,
        }
        for user_id in sorted(recipient_ids):
            await manager.send_personal_message(payload, str(user_id))

        return nuevo_pago


class NotificationService:
    @staticmethod
    async def send_push_notification(
        db: Session,
        user_id: int,
        titulo: str,
        mensaje: str,
    ):
        """
        CU16 · Envia una notificacion push simulada via WebSocket.
        """
        nueva_notif = Notificacion(
            usuario_id=user_id,
            titulo=titulo,
            mensaje=mensaje,
            tipo="push",
        )
        db.add(nueva_notif)
        db.commit()

        await manager.send_personal_message(
            {
                "type": "notification",
                "titulo": titulo,
                "mensaje": mensaje,
                "timestamp": str(nueva_notif.creado_at),
            },
            str(user_id),
        )

        return nueva_notif
