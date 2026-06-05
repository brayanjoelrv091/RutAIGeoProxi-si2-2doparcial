"""
P5 — Rutas de Pagos y Notificaciones (CU16, CU17, CU18).
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.shared.deps import get_current_user, get_db, get_token_credentials
from app.shared.security import jwt_payload_safe
from app.modules.p1_usuarios.models import Usuario
from app.modules.p5_pagos.schemas import PagoCreate, PagoResponse, NotificacionResponse
from app.modules.p5_pagos.services import PaymentService, NotificationService
from app.shared.websocket_manager import manager

router = APIRouter(prefix="/payments", tags=["P5 · Pagos y Notificaciones"])

@router.post("/process", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def process_payment(
    pago_in: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    CU18 · Procesar pago en línea (Simulado).
    """
    return await PaymentService.process_payment(db, pago_in, current_user)

@router.get("/history", response_model=List[PagoResponse])
def get_payment_history(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista historial de pagos.
    """
    from app.modules.p5_pagos.models import Pago
    from app.modules.p2_incidentes.models import Incidente
    
    query = db.query(Pago)
    
    # Si es cliente, filtrar por sus incidentes
    if current_user.rol == "cliente":
        query = query.join(Incidente).filter(Incidente.usuario_id == current_user.id)
    
    # Si es taller, filtrar por sus incidentes asignados (opcional, pero buena práctica)
    # elif current_user.rol == "taller":
    #     ...
        
    return query.all()

# --- Rutas de Notificaciones ---

@router.get("/notifications", response_model=List[NotificacionResponse])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener las notificaciones del usuario actual.
    """
    from app.modules.p5_pagos.models import Notificacion
    return db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id).order_by(Notificacion.creado_at.desc()).all()

@router.delete("/notifications/all", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_notifications(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.modules.p5_pagos.models import Notificacion
    db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id).delete()
    db.commit()
    return None

@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from app.modules.p5_pagos.models import Notificacion
    notif = db.query(Notificacion).filter(
        Notificacion.id == notification_id,
        Notificacion.usuario_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    db.delete(notif)
    db.commit()
    return None

@router.websocket("/ws/notifications/{user_id}")
async def notifications_websocket(websocket: WebSocket, user_id: int):
    """
    CU16/CU17 · WebSocket para recibir notificaciones push y actualizaciones de estado.
    Requiere autenticación JWT.
    """
    # Autenticación basada en token query param
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Token requerido")
        return
    
    payload = jwt_payload_safe(token)
    if not payload:
        await websocket.close(code=4001, reason="Token inválido")
        return
    
    # Verificar que el user_id del path coincida con el token
    token_user_id = int(payload.get("sub"))
    if token_user_id != user_id:
        await websocket.close(code=4003, reason="User ID no coincide con token")
        return
    
    await manager.connect(websocket, str(user_id))
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, str(user_id))
