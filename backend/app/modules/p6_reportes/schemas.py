from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReporteBase(BaseModel):
    nombre_archivo: str
    tipo_reporte: str

class ReporteCreate(ReporteBase):
    generado_por_id: Optional[int] = None
    ruta_archivo: Optional[str] = None

class ReporteResponse(ReporteBase):
    id: int
    fecha_generacion: datetime
    ruta_archivo: Optional[str]

    model_config = {"from_attributes": True}
