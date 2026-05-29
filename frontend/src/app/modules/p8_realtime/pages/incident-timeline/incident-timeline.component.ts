import { Component, OnInit, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../../../environment';

/**
 * P8 · CU-25 — Componente Timeline visual de estados del incidente.
 *
 * Muestra el historial completo de transiciones de estado con:
 *   - Línea de tiempo vertical con nodos coloreados por estado
 *   - Actor que realizó cada cambio
 *   - Timestamp de cada transición
 *   - Estado actual y transiciones disponibles
 */

interface TimelineEvent {
  id: number;
  estado_anterior: string;
  estado_nuevo: string;
  label_anterior: string;
  label_nuevo: string;
  actor_id: number | null;
  actor_rol: string | null;
  notas: string | null;
  creado_en: string;
}

interface TimelineData {
  incidente_id: number;
  estado_actual: string;
  label_actual: string;
  es_terminal: boolean;
  transiciones_disponibles: string[];
  eventos: TimelineEvent[];
}

@Component({
  selector: 'app-incident-timeline',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './incident-timeline.component.html',
  styleUrls: ['./incident-timeline.component.css'],
})
export class IncidentTimelineComponent implements OnInit {
  @Input() incidentId!: number;
  @Input() token!: string;

  timeline: TimelineData | null = null;
  loading = true;
  error: string | null = null;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    if (this.incidentId && this.token) {
      this.loadTimeline();
    }
  }

  loadTimeline(): void {
    this.loading = true;
    this.error = null;

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${this.token}`,
    });

    this.http.get<TimelineData>(
      `${environment.apiUrl}/realtime/incidents/${this.incidentId}/timeline`,
      { headers }
    ).subscribe({
      next: (data) => {
        this.timeline = data;
        this.loading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Error cargando timeline';
        this.loading = false;
      },
    });
  }

  getStateColor(state: string): string {
    const colors: Record<string, string> = {
      'pendiente': '#f59e0b',
      'buscando_taller': '#3b82f6',
      'taller_asignado': '#8b5cf6',
      'en_camino': '#06b6d4',
      'en_atencion': '#f97316',
      'finalizado': '#22c55e',
      'cancelado': '#ef4444',
      'sin_estado': '#6b7280',
    };
    return colors[state] || '#6b7280';
  }

  getRolIcon(rol: string | null): string {
    const icons: Record<string, string> = {
      'admin': '👤',
      'taller': '🏪',
      'cliente': '🚗',
      'sistema': '⚙️',
    };
    return icons[rol || ''] || '👤';
  }

  formatTime(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-BO', { day: '2-digit', month: 'short', year: 'numeric' });
  }
}
