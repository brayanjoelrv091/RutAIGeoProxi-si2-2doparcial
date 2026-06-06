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
from app.modules.p8_realtime.models import EventoEstado
from app.modules.p1_usuarios.models import Usuario

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

        # Para tiempo de resolución y SLA (Cotizacion.tiempo_estimado_dias)
        res_query = inc_query.filter(Incidente.estado == "finalizado").all()
        tiempo_res_min = 0.0
        sla_cumplidos = 0
        talleres_stats = {}
        tiempo_llegada_min_total = 0.0
        count_llegada = 0

        for r in res_query:
            if r.actualizado_en and r.creado_en:
                diff = r.actualizado_en - r.creado_en
                tiempo_res_min += diff.total_seconds() / 60.0
                
                # Check SLA
                cot = db.query(Cotizacion).filter(Cotizacion.incidente_id == r.id).first()
                if cot and cot.tiempo_estimado_dias:
                    dias_reales = diff.total_seconds() / 86400.0
                    if dias_reales <= cot.tiempo_estimado_dias:
                        sla_cumplidos += 1
                        
            # Check taller efficiency
            asig = db.query(Asignacion).filter(Asignacion.incidente_id == r.id).first()
            if asig:
                taller = db.query(Usuario).filter(Usuario.id == asig.taller_id).first()
                if taller:
                    if taller.nombre not in talleres_stats:
                        talleres_stats[taller.nombre] = {"count": 0, "total_min": 0}
                    talleres_stats[taller.nombre]["count"] += 1
                    talleres_stats[taller.nombre]["total_min"] += diff.total_seconds() / 60.0 if r.actualizado_en and r.creado_en else 0
                    
            # Check tiempo promedio llegada (taller_asignado -> en_atencion)
            evento_asignado = db.query(EventoEstado).filter(EventoEstado.incidente_id == r.id, EventoEstado.estado_nuevo == "taller_asignado").first()
            evento_llegada = db.query(EventoEstado).filter(EventoEstado.incidente_id == r.id, EventoEstado.estado_nuevo == "en_atencion").first()
            if evento_asignado and evento_llegada:
                diff_llegada = evento_llegada.creado_en - evento_asignado.creado_en
                tiempo_llegada_min_total += diff_llegada.total_seconds() / 60.0
                count_llegada += 1

        avg_resolucion = (tiempo_res_min / len(res_query)) if res_query else 0.0
        avg_llegada = (tiempo_llegada_min_total / count_llegada) if count_llegada > 0 else 0.0
        nivel_sla = (sla_cumplidos / len(res_query)) * 100 if res_query else 0.0

        talleres_eficientes = []
        for t_nombre, stats in talleres_stats.items():
            if stats["count"] > 0:
                avg = stats["total_min"] / stats["count"]
                talleres_eficientes.append({"nombre": t_nombre, "avg_resolucion_min": round(avg, 2)})
        
        # Sort by best time (lowest is better)
        talleres_eficientes.sort(key=lambda x: x["avg_resolucion_min"])

        # Zonas calientes (agrupadas por cuadrante de aprox 1km -> round a 2 decimales)
        zonas_dict = {}
        for inc in incidentes:
            if inc.latitud and inc.longitud:
                coord = f"{round(inc.latitud, 2)}, {round(inc.longitud, 2)}"
                zonas_dict[coord] = zonas_dict.get(coord, 0) + 1
                
        zonas_calientes = [{"coordenadas": k, "cantidad": v} for k, v in zonas_dict.items()]
        zonas_calientes.sort(key=lambda x: x["cantidad"], reverse=True)

        return DashboardKPIs(
            tenant_id=tenant_id,
            total_incidentes=total_incidentes,
            completados=completados,
            cancelados=cancelados,
            tiempo_promedio_asignacion_min=round(avg_asignacion, 2),
            tiempo_promedio_resolucion_min=round(avg_resolucion, 2),
            tiempo_promedio_llegada_min=round(avg_llegada, 2),
            nivel_cumplimiento_sla=round(nivel_sla, 2),
            incidentes_por_categoria=cat_counts,
            incidentes_por_severidad=sev_counts,
            talleres_mas_eficientes=talleres_eficientes[:5], # Top 5
            zonas_calientes=zonas_calientes[:10], # Top 10
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
