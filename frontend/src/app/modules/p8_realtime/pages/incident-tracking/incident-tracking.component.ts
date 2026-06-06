import { Component, OnInit, OnDestroy, Input, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { RealtimeService, WSMessage } from '../../realtime.service';

import * as L from 'leaflet';

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
export class IncidentTrackingComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() incidentId!: number;
  @Input() token!: string;

  // ── Estado del componente ──
  connectionState: string = 'disconnected';
  lastPosition: { lat: number; lng: number; role: string; timestamp: string } | null = null;
  positions: Array<{ lat: number; lng: number; role: string; timestamp: string }> = [];
  speed: number = 0;
  heading: number = 0;

  // ── Mapa Leaflet ──
  private map: L.Map | undefined;
  private tileLayer: L.TileLayer | undefined;
  private marker: L.Marker | undefined;
  private pathLine: L.Polyline | undefined;
  private themeObserver: MutationObserver | undefined;

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

  ngAfterViewInit(): void {
    this.initMap();
  }

  private initMap(): void {
    // Default to Santa Cruz, Bolivia
    this.map = L.map('leaflet-map').setView([-17.7833, -63.1821], 13);
    
    const isLight = document.body.classList.contains('light-theme');
    const tileUrl = isLight 
      ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

    this.tileLayer = L.tileLayer(tileUrl, {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 20
    }).addTo(this.map);

    this.themeObserver = new MutationObserver(() => {
      if (this.tileLayer) {
        const light = document.body.classList.contains('light-theme');
        this.tileLayer.setUrl(light 
          ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
          : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
        );
      }
    });
    this.themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    this.pathLine = L.polyline([], { color: '#00F2FF', weight: 4 }).addTo(this.map);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    if (this.themeObserver) {
      this.themeObserver.disconnect();
    }
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

    // Actualizar Mapa Leaflet
    if (this.map && this.pathLine) {
      const latLng = L.latLng(point.lat, point.lng);
      
      if (!this.marker) {
        // Inicializar marcador
        const iconHtml = `<div style="font-size: 24px; text-shadow: 0 0 10px #00F2FF;">${point.role === 'tecnico' ? '🔧' : '🚗'}</div>`;
        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'custom-leaflet-icon',
          iconSize: [30, 30],
          iconAnchor: [15, 15]
        });
        this.marker = L.marker(latLng, { icon: customIcon }).addTo(this.map);
        this.map.setView(latLng, 16);
      } else {
        this.marker.setLatLng(latLng);
        this.map.panTo(latLng);
      }

      this.pathLine.addLatLng(latLng);
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
