import { Component, OnInit, OnDestroy, Input, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, interval } from 'rxjs';
import { RealtimeService, WSMessage } from '../../realtime.service';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environment';

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
  private incidentMarker: L.Marker | undefined;
  private routeLine: L.Polyline | undefined;
  private incidentLoc: { lat: number, lng: number } | null = null;
  private lastRouteFetch = 0;
  private themeObserver: MutationObserver | undefined;
  private subs: Subscription[] = [];
  
  constructor(private realtime: RealtimeService, private http: HttpClient) {}

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

      // Fetch incident details to get destination
      this.http.get<any>(`${environment.apiUrl}/api/v1/incidents/${this.incidentId}`).subscribe({
        next: (inc) => {
          this.incidentLoc = { lat: inc.latitud, lng: inc.longitud };
          this.plotIncidentMarker();
        },
        error: (e) => console.error('Error fetching incident for routing', e)
      });
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

      // Update route using OSRM every 10 seconds
      const now = Date.now();
      if (this.incidentLoc && now - this.lastRouteFetch > 10000) {
        this.lastRouteFetch = now;
        this.fetchRoute(point.lat, point.lng, this.incidentLoc.lat, this.incidentLoc.lng);
      }
    }
  }

  private plotIncidentMarker() {
    if (!this.map || !this.incidentLoc) return;
    const latLng = L.latLng(this.incidentLoc.lat, this.incidentLoc.lng);
    const iconHtml = `<div style="font-size: 24px; text-shadow: 0 0 10px #FF3D00; animation: pulse 1s infinite;">🚨</div>`;
    const customIcon = L.divIcon({
      html: iconHtml,
      className: 'custom-leaflet-icon',
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });
    this.incidentMarker = L.marker(latLng, { icon: customIcon }).addTo(this.map);
    this.incidentMarker.bindPopup('<b style="color:#FF3D00;">Lugar del Incidente</b>');
  }

  private fetchRoute(lat1: number, lng1: number, lat2: number, lng2: number) {
    const url = `https://router.project-osrm.org/route/v1/driving/${lng1},${lat1};${lng2},${lat2}?overview=full&geometries=geojson`;
    this.http.get<any>(url).subscribe({
      next: (res) => {
        if (res.routes && res.routes.length > 0) {
          const coords = res.routes[0].geometry.coordinates;
          const latLngs = coords.map((c: number[]) => L.latLng(c[1], c[0]));
          
          if (this.routeLine) {
            this.routeLine.setLatLngs(latLngs);
          } else if (this.map) {
            this.routeLine = L.polyline(latLngs, { color: '#00C853', weight: 5, dashArray: '10, 10' }).addTo(this.map);
          }
        }
      },
      error: (e) => console.error('OSRM Route error', e)
    });
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
