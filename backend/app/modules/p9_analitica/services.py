"""
P9 — Servicios de Analítica y Operaciones.
"""

import math
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.p2_incidentes.models import Incidente, ClasificacionIncidente
from app.modules.p4_asignacion.models import Asignacion
from app.modules.p9_analitica.models import Cotizacion, CotizacionItem
from app.modules.p9_analitica.schemas import DashboardKPIs, TiempoEstimadoOut

class DashboardService:
    @staticmethod
    def get_kpis(db: Session, tenant_id: int | None) -> DashboardKPIs:
        # Filtrado por tenant_id
        inc_query = db.query(Incidente)
        if tenant_id is not None:
            inc_query = inc_query.filter(Incidente.tenant_id == tenant_id)
        else:
            inc_query = inc_query.filter(Incidente.tenant_id.is_(None))

        total_incidentes = inc_query.count()
        completados = inc_query.filter(Incidente.estado == "finalizado").count()
        cancelados = inc_query.filter(Incidente.estado == "cancelado").count()
        
        # Categorías y severidades
        incidentes = inc_query.all()
        cat_counts = {}
        sev_counts = {}
        for inc in incidentes:
            if inc.categoria:
                cat_counts[inc.categoria] = cat_counts.get(inc.categoria, 0) + 1
            if inc.severidad:
                sev_counts[inc.severidad] = sev_counts.get(inc.severidad, 0) + 1

        # Tiempo promedio asignación (aproximado usando Asignacion)
        asig_query = db.query(Asignacion)
        # Filtro de asig_query vía JOIN
        if tenant_id is not None:
            asig_query = asig_query.join(Incidente).filter(Incidente.tenant_id == tenant_id)
        else:
            asig_query = asig_query.join(Incidente).filter(Incidente.tenant_id.is_(None))

        asignaciones = asig_query.all()
        tiempo_total_min = 0.0
        count_asig = 0
        for asig in asignaciones:
            # Aproximación: diferencia entre creado_en de incidente y asignado_en
            inc = asig.incidente
            if inc and asig.asignado_en and inc.creado_en:
                diff = asig.asignado_en - inc.creado_en
                tiempo_total_min += diff.total_seconds() / 60.0
                count_asig += 1

        avg_asignacion = (tiempo_total_min / count_asig) if count_asig > 0 else 0.0

        # Para tiempo de resolución no hay fechas estrictas de "finalizado_en" por ahora, usaremos actualizado_en
        res_query = inc_query.filter(Incidente.estado == "finalizado").all()
        tiempo_res_min = 0.0
        for r in res_query:
            if r.actualizado_en and r.creado_en:
                diff = r.actualizado_en - r.creado_en
                tiempo_res_min += diff.total_seconds() / 60.0
        avg_resolucion = (tiempo_res_min / len(res_query)) if res_query else 0.0

        return DashboardKPIs(
            tenant_id=tenant_id,
            total_incidentes=total_incidentes,
            completados=completados,
            cancelados=cancelados,
            tiempo_promedio_asignacion_min=round(avg_asignacion, 2),
            tiempo_promedio_resolucion_min=round(avg_resolucion, 2),
            incidentes_por_categoria=cat_counts,
            incidentes_por_severidad=sev_counts,
        )


class EstimacionService:
    @staticmethod
    def calcular_tiempo_estimado(db: Session, incidente_id: int) -> TiempoEstimadoOut:
        """Calcula el tiempo estimado basado en IA/clasificación."""
        clasificacion = db.query(ClasificacionIncidente).filter(
            ClasificacionIncidente.incidente_id == incidente_id
        ).first()

        if not clasificacion:
            return TiempoEstimadoOut(
                incidente_id=incidente_id,
                tiempo_estimado_dias=2,
                rango_dias="1-3 días",
                razonamiento="Sin clasificación IA, tiempo base por defecto."
            )

        cat = clasificacion.categoria.lower()
        sev = clasificacion.severidad.lower()
        
        base = 1
        if "carroceria" in cat or "choque" in cat:
            base = 5
        elif "motor" in cat or "mecanico" in cat:
            base = 3
            
        if sev == "grave":
            base += 3
        elif sev == "critico":
            base += 5
            
        return TiempoEstimadoOut(
            incidente_id=incidente_id,
            tiempo_estimado_dias=base,
            rango_dias=f"{max(1, base-1)}-{base+2} días",
            razonamiento=f"Categoría '{cat}' y severidad '{sev}' requieren aprox {base} días."
        )


class CotizacionService:
    @staticmethod
    def generar_cotizacion_desde_ia(db: Session, incidente_id: int) -> Cotizacion:
        """Genera una cotización base usando la IA del incidente."""
        
        # Verificar que no exista ya
        existente = db.query(Cotizacion).filter(Cotizacion.incidente_id == incidente_id).first()
        if existente:
            return existente
            
        incidente = db.query(Incidente).filter(Incidente.id == incidente_id).first()
        if not incidente:
            raise HTTPException(status_code=404, detail="Incidente no encontrado")
            
        clasificacion = db.query(ClasificacionIncidente).filter(
            ClasificacionIncidente.incidente_id == incidente_id
        ).first()
        
        # Cotización base
        cot = Cotizacion(
            incidente_id=incidente_id,
            tenant_id=incidente.tenant_id,
            estado="borrador"
        )
        db.add(cot)
        db.commit()
        db.refresh(cot)
        
        # Calcular items basados en IA
        items = []
        if clasificacion:
            cat = clasificacion.categoria.lower()
            sev = clasificacion.severidad.lower()
            
            # Costo base por diagnostico
            items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Diagnóstico Técnico Asistido", cantidad=1, precio_unitario=50.0))
            
            if sev == "grave" or sev == "critico":
                items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Servicio de Grúa/Remolque", cantidad=1, precio_unitario=150.0))
                items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Mano de obra especializada (Estimación)", cantidad=10, precio_unitario=40.0))
            else:
                items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Mano de obra general (Estimación)", cantidad=3, precio_unitario=35.0))
                
            if "carroceria" in cat:
                items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Repuestos Carrocería (Estimación)", cantidad=1, precio_unitario=300.0))
            elif "motor" in cat:
                items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Repuestos de Motor (Estimación)", cantidad=1, precio_unitario=500.0))
        else:
            items.append(CotizacionItem(cotizacion_id=cot.id, descripcion="Revisión General", cantidad=1, precio_unitario=80.0))
            
        for item in items:
            db.add(item)
            
        # Calcular totales
        subtotal = sum(i.cantidad * i.precio_unitario for i in items)
        iva = subtotal * 0.16 # 16% IVA
        total = subtotal + iva
        
        cot.subtotal = subtotal
        cot.iva = iva
        cot.total = total
        
        # Tiempo estimado
        est = EstimacionService.calcular_tiempo_estimado(db, incidente_id)
        cot.tiempo_estimado_dias = est.tiempo_estimado_dias
        
        db.commit()
        db.refresh(cot)
        return cot
        
    @staticmethod
    def get_cotizacion(db: Session, cotizacion_id: int) -> Cotizacion:
        cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
        if not cot:
            raise HTTPException(status_code=404, detail="Cotización no encontrada")
        return cot
