from sqlalchemy import create_engine, text
from app.shared.database import Base
from app.modules.p1_usuarios.models import Usuario, Vehiculo
from app.modules.p2_incidentes.models import Incidente, ClasificacionIncidente
from app.modules.p3_talleres.models import Taller, Tecnico, SolicitudServicio
from app.modules.p4_asignacion.models import Asignacion
from app.modules.p5_pagos.models import Pago, Notificacion
from app.shared.config import settings

engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    print("Migrando DB...")
    try:
        conn.execute(text('ALTER TABLE incidentes ADD COLUMN tipo_busqueda VARCHAR(30) DEFAULT \'general\' NOT NULL;'))
        print("Añadido tipo_busqueda a incidentes")
    except Exception as e:
        print(e)
    try:
        conn.execute(text('ALTER TABLE incidentes ADD COLUMN taller_preferido_id INTEGER REFERENCES talleres(id) ON DELETE SET NULL;'))
        print("Añadido taller_preferido_id a incidentes")
    except Exception as e:
        print(e)
    conn.commit()

print("Creando nuevas tablas (usuarios_talleres_favoritos)...")
Base.metadata.create_all(bind=engine)
print("¡Migración completada!")
