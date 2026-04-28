from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PagoBase(BaseModel):
    incidente_id: int
    monto: float
    moneda: str = "USD"
    metodo_pago: str

class PagoCreate(PagoBase):
    pass

class PagoResponse(PagoBase):
    id: int
    estado: str
    transaccion_id: Optional[str]
    creado_at: datetime

    model_config = {"from_attributes": True}

class NotificacionBase(BaseModel):
    usuario_id: int
    titulo: str
    mensaje: str
    tipo: str = "push"

class NotificacionResponse(NotificacionBase):
    id: int
    leido: bool
    creado_at: datetime

    class Config:
        from_attributes = True
