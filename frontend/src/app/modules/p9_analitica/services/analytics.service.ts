import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environment';

export interface DashboardKPIs {
  tenant_id: number | null;
  total_incidentes: number;
  completados: number;
  cancelados: number;
  tiempo_promedio_asignacion_min: number;
  tiempo_promedio_resolucion_min: number;
  tiempo_promedio_llegada_min: number;
  nivel_cumplimiento_sla: number;
  incidentes_por_categoria: { [key: string]: number };
  incidentes_por_severidad: { [key: string]: number };
  talleres_mas_eficientes: { nombre: string; avg_resolucion_min: number }[];
  zonas_calientes: { coordenadas: string; cantidad: number }[];
}

@Injectable({
  providedIn: 'root'
})
export class AnalyticsService {
  private apiUrl = `${environment.apiUrl}/analytics`;

  constructor(private http: HttpClient) {}

  getDashboardKPIs(): Observable<DashboardKPIs> {
    return this.http.get<DashboardKPIs>(`${this.apiUrl}/dashboard`);
  }
}
