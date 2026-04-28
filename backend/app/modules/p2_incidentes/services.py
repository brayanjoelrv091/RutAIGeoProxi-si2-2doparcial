"""
P2 — Capa de servicios de Incidentes (CU7, CU8, CU9).
"""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload

from app.modules.p2_incidentes.classifier import ClassificationResult, get_classifier
from app.modules.p2_incidentes.models import (
    ClasificacionIncidente,
    Incidente,
    IncidenteMedia,
)
from app.modules.p2_incidentes.schemas import IncidentCreate
from app.modules.p6_auditoria.services import AuditService
from app.shared.storage import upload_file

logger = logging.getLogger(__name__)


class IncidentService:
    """Servicio de gestión de incidentes vehiculares."""

    @staticmethod
    async def create(
        db: Session,
        user_id: int,
        payload: IncidentCreate,
        fotos: list[UploadFile] | None = None,
        audio: UploadFile | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> Incidente:
        """
        CU7 — Reportar incidente con fotos, audio y ubicación GPS.
        Ejecuta clasificación automática (CU8) tras la creación.
        """
        # 1. Crear incidente
        incidente = Incidente(
            usuario_id=user_id,
            titulo=payload.titulo,
            descripcion=payload.descripcion,
            latitud=payload.latitud,
            longitud=payload.longitud,
            direccion=payload.direccion,
            estado="nuevo",
        )
        db.add(incidente)
        db.flush()  # Obtener ID sin commit

        # 2. Subir fotos
        image_local_paths: list[str] = []
        temp_dirs: list[str] = []
        if fotos:
            for foto in fotos[:5]:  # Máximo 5 fotos
                url = await upload_file(foto, folder=f"incidentes/{incidente.id}/fotos")
                db.add(
                    IncidenteMedia(
                        incidente_id=incidente.id,
                        tipo_medio="foto",
                        url_archivo=url,
                    )
                )
                # Guardar copia temporal para YOLOv8
                if foto.filename:
                    temp_dir = tempfile.mkdtemp()
                    temp_dirs.append(temp_dir)
                    tmp = Path(temp_dir) / foto.filename
                    await foto.seek(0)
                    content = await foto.read()
                    tmp.write_bytes(content)
                    image_local_paths.append(str(tmp))

        # 3. Subir audio
        audio_local_path: str | None = None
        audio_temp_dir: str | None = None
        if audio:
            url = await upload_file(audio, folder=f"incidentes/{incidente.id}/audio")
            incidente.url_audio = url
            db.add(
                IncidenteMedia(
                    incidente_id=incidente.id,
                    tipo_medio="audio",
                    url_archivo=url,
                )
            )
            # Guardar copia temporal para Whisper
            if audio.filename:
                audio_temp_dir = tempfile.mkdtemp()
                tmp = Path(audio_temp_dir) / audio.filename
                await audio.seek(0)
                content = await audio.read()
                tmp.write_bytes(content)
                audio_local_path = str(tmp)

        # 4. Clasificación automática (CU8)
        try:
            classifier = get_classifier()
            result: ClassificationResult = await classifier.classify(
                text=f"{payload.titulo} {payload.descripcion or ''}",
                image_paths=image_local_paths if image_local_paths else None,
                audio_path=audio_local_path,
            )
            incidente.categoria = result.categoria
            incidente.severidad = result.severidad

            # Lógica de Incertidumbre (Requerimiento Examen 1)
            if result.confianza < 0.5:
                incidente.estado = "incierto"
            else:
                incidente.estado = "clasificado"

            db.add(
                ClasificacionIncidente(
                    incidente_id=incidente.id,
                    categoria=result.categoria,
                    severidad=result.severidad,
                    confianza=result.confianza,
                    razonamiento=result.razonamiento,
                    metodo=result.metodo,
                )
            )
        except Exception:
            logger.exception("Error en clasificación automática")
            # No falla la creación del incidente si la IA falla

        db.commit()
        db.refresh(incidente)

        # Auditoría (CU19)
        AuditService.log(
            db,
            usuario_id=user_id,
            rol="cliente",
            accion=f"Reporte de incidente #{incidente.id} ({incidente.categoria})"
        )

        # Limpiar archivos temporales
        for p in image_local_paths:
            try:
                Path(p).unlink(missing_ok=True)
            except OSError:
                pass
        if audio_local_path:
            try:
                Path(audio_local_path).unlink(missing_ok=True)
            except OSError:
                pass
        # Limpiar directorios temporales
        for temp_dir in temp_dirs:
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass
        if audio_temp_dir:
            try:
                os.rmdir(audio_temp_dir)
            except OSError:
                pass

        # 5. ASIGNACIÓN AUTOMÁTICA (REQUERIMIENTO INTELIGENTE)
        if incidente.estado == "clasificado":
            try:
                from app.modules.p4_asignacion.services import AssignmentService
                # Intentar asignar automáticamente en el radio por defecto (50km)
                AssignmentService.auto_assign(db, incidente.id, background_tasks=background_tasks)
                
                # Auditoría de asignación automática
                AuditService.log(
                    db,
                    accion=f"Asignación automática disparada para incidente #{incidente.id}",
                    rol="Sistema"
                )
            except Exception as e:
                logger.error(f"No se pudo auto-asignar incidente #{incidente.id}: {e}")

        return incidente

    @staticmethod
    def get_detail(db: Session, incident_id: int, user_id: int | None = None) -> Incidente:
        """
        CU9 — Ficha técnica estructurada del incidente.
        Si user_id se proporciona, valida que sea el dueño (o admin).
        """
        query = (
            db.query(Incidente)
            .options(
                joinedload(Incidente.medios),
                joinedload(Incidente.clasificacion),
            )
            .filter(Incidente.id == incident_id)
        )

        incidente = query.first()
        if not incidente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidente no encontrado",
            )

        # Validación de propiedad (Security check)
        # Se permite si no hay user_id (pista de admin) o si coincide con el dueño
        if user_id and incidente.usuario_id != user_id:
            # Aquí podríamos verificar el rol si pasáramos el objeto usuario completo, 
            # pero por ahora el llamador (route) decide si pasa el user_id para validar.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver este incidente",
            )

        return incidente

    @staticmethod
    def list_by_user(db: Session, user_id: int) -> list[Incidente]:
        """Listar incidentes del usuario autenticado."""
        return (
            db.query(Incidente)
            .filter(Incidente.usuario_id == user_id)
            .order_by(Incidente.creado_en.desc())
            .all()
        )

    @staticmethod
    def list_all(db: Session) -> list[Incidente]:
        """Listar todos los incidentes (admin)."""
        return db.query(Incidente).order_by(Incidente.creado_en.desc()).all()

    @staticmethod
    async def reclassify(db: Session, incident_id: int) -> ClasificacionIncidente:
        """CU8 — Re-clasificar manualmente un incidente existente."""
        incidente = (
            db.query(Incidente)
            .options(joinedload(Incidente.medios))
            .filter(Incidente.id == incident_id)
            .first()
        )
        if not incidente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incidente no encontrado",
            )

        # Recopilar datos para clasificación
        text = f"{incidente.titulo} {incidente.descripcion or ''}"

        classifier = get_classifier()
        result = await classifier.classify(text=text)

        # Actualizar o crear clasificación
        existing = (
            db.query(ClasificacionIncidente)
            .filter(ClasificacionIncidente.incidente_id == incident_id)
            .first()
        )
        if existing:
            existing.categoria = result.categoria
            existing.severidad = result.severidad
            existing.confianza = result.confianza
            existing.razonamiento = result.razonamiento
            existing.metodo = result.metodo
            clasificacion = existing
        else:
            clasificacion = ClasificacionIncidente(
                incidente_id=incident_id,
                categoria=result.categoria,
                severidad=result.severidad,
                confianza=result.confianza,
                razonamiento=result.razonamiento,
                metodo=result.metodo,
            )
            db.add(clasificacion)

        incidente.categoria = result.categoria
        incidente.severidad = result.severidad
        incidente.estado = "clasificado"
        db.commit()
        db.refresh(clasificacion)
        return clasificacion
