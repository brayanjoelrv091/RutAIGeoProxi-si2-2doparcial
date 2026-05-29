import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { RealtimeService, WSMessage } from '../../realtime.service';

/**
 * P8 · CU-26 — Componente de tracking GPS en vivo.
 *
 * Muestra la posición del técnico en un mapa y actualiza en tiempo real
 * vía WebSocket. Incluye indicador de velocidad y heading.
 */
@Component({
  selector: 'app-incident-tracking',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './incident-tracking.component.html',
  styleUrls: ['./incident-tracking.component.css'],
})
export class IncidentTrackingComponent implements OnInit, OnDestroy {
  @Input() incidentId!: number;
  @Input() token!: string;

  // ── Estado del componente ──
  connectionState: string = 'disconnected';
  lastPosition: { lat: number; lng: number; role: string; timestamp: string } | null = null;
  positions: Array<{ lat: number; lng: number; role: string; timestamp: string }> = [];
  speed: number = 0;
  heading: number = 0;

  private subs: Subscription[] = [];

  constructor(private realtime: RealtimeService) {}

  ngOnInit(): void {
    if (this.incidentId && this.token) {
      this.realtime.connectToIncident(this.incidentId, this.token);

      this.subs.push(
        this.realtime.state$.subscribe(state => {
          this.connectionState = state;
        })
      );

      this.subs.push(
        this.realtime.onMessage$.subscribe((msg: WSMessage) => {
          if (msg.type === 'location_update') {
            this.handleLocationUpdate(msg);
          }
        })
      );
    }
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    this.realtime.disconnect();
  }

  private handleLocationUpdate(msg: any): void {
    const point = {
      lat: msg.lat,
      lng: msg.lng,
      role: msg.role || 'tecnico',
      timestamp: msg.timestamp || new Date().toISOString(),
    };

    this.lastPosition = point;
    this.positions.push(point);
    this.speed = msg.velocidad_kmh || 0;
    this.heading = msg.heading || 0;

    // Mantener últimos 200 puntos para rendimiento
    if (this.positions.length > 200) {
      this.positions = this.positions.slice(-200);
    }
  }

  get connectionIcon(): string {
    switch (this.connectionState) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'reconnecting': return '🟠';
      default: return '🔴';
    }
  }

  get headingLabel(): string {
    if (this.heading >= 337.5 || this.heading < 22.5) return 'N';
    if (this.heading >= 22.5 && this.heading < 67.5) return 'NE';
    if (this.heading >= 67.5 && this.heading < 112.5) return 'E';
    if (this.heading >= 112.5 && this.heading < 157.5) return 'SE';
    if (this.heading >= 157.5 && this.heading < 202.5) return 'S';
    if (this.heading >= 202.5 && this.heading < 247.5) return 'SO';
    if (this.heading >= 247.5 && this.heading < 292.5) return 'O';
    return 'NO';
  }
}
