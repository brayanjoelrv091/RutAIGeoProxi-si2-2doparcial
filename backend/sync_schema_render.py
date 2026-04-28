from sqlalchemy import create_engine
from app.shared.database import Base
# Importar todos los modelos para que Base los conozca
from app.modules.p1_usuarios.models import Usuario, Vehiculo
from app.modules.p2_incidentes.models import Incidente, ClasificacionIncidente
from app.modules.p3_talleres.models import Taller, Tecnico, SolicitudServicio
from app.modules.p4_asignacion.models import Asignacion
from app.modules.p5_pagos.models import Pago, Notificacion

RENDER_DB_URL = "postgresql://rutai_db_user:tRtlGpIRVZJqeznt5DXpIRnM00b9ly7v@dpg-d7nbd8dckfvc73et4mjg-a.oregon-postgres.render.com/rutai_db"

engine = create_engine(RENDER_DB_URL)

print("Eliminando tablas existentes en Render...")
Base.metadata.drop_all(bind=engine)
print("Tablas eliminadas.")

print("Recreando tablas con el esquema nuevo...")
Base.metadata.create_all(bind=engine)
print("¡Esquema actualizado exitosamente!")
