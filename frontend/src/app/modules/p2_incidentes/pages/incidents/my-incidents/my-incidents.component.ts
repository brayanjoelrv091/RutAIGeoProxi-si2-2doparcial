import { SlicePipe } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Incident, IncidentService } from '../../../incident.service';
import { AssignmentService } from '../../../../p4_asignacion/assignment.service';

@Component({
  selector: 'app-my-incidents',
  standalone: true,
  imports: [RouterLink, SlicePipe],
  templateUrl: './my-incidents.component.html',
  styleUrl: './my-incidents.component.css',
})
export class MyIncidentsComponent implements OnInit {
  private readonly incidentSvc = inject(IncidentService);
  private readonly assignmentSvc = inject(AssignmentService);

  incidents: Incident[] = [];
  error = '';
  assignMessage = '';
  is_admin = false;
  is_cliente = false;
  is_taller = false;

  ngOnInit(): void {
    const role = sessionStorage.getItem('user_role');
    this.is_admin = role === 'admin';
    this.is_cliente = role === 'cliente';
    this.is_taller = role === 'taller';
    this.load();
  }

  load(): void {
    const obs = this.is_admin ? this.incidentSvc.listAllIncidents() : this.incidentSvc.listMyIncidents();
    
    obs.subscribe({
      next: (list) => (this.incidents = list),
      error: () => (this.error = 'Error al cargar incidentes'),
    });
  }

  badgeClass(estado: string): string {
    const map: Record<string, string> = {
      nuevo: 'badge-new', clasificado: 'badge-classified', asignado: 'badge-assigned',
      en_proceso: 'badge-process', resuelto: 'badge-resolved',
    };
    return map[estado] || 'badge-default';
  }

  severityClass(sev: string | null): string {
    if (!sev) return '';
    const map: Record<string, string> = {
      leve: 'sev-low', moderado: 'sev-mid', grave: 'sev-high', critico: 'sev-critical',
    };
    return map[sev] || '';
  }

  autoAssign(incidentId: number): void {
    this.assignMessage = '';
    this.assignmentSvc.autoAssign(incidentId).subscribe({
      next: (res) => {
        this.assignMessage = res.message;
        this.load();
      },
      error: (e) => (this.assignMessage = e?.error?.detail || 'Error en asignación'),
    });
  }
}
