import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environment';

import * as L from 'leaflet';
import 'leaflet.heat';

@Component({
  selector: 'app-map-explorer',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './map-explorer.component.html',
  styleUrls: ['./map-explorer.component.css']
})
export class MapExplorerComponent implements OnInit, AfterViewInit, OnDestroy {
  searchQuery = '';
  showHeatmap = false;
  searchResults: any[] = [];
  
  private map: L.Map | undefined;
  private tileLayer: L.TileLayer | undefined;
  private themeObserver: MutationObserver | undefined;
  
  private workshopLayer: L.LayerGroup = L.layerGroup();
  private heatLayer: any; // L.heatLayer
  private heatData: any[] = [];

  constructor(private http: HttpClient) {}

  ngOnInit() {}

  ngAfterViewInit() {
    this.initMap();
    this.loadWorkshops();
  }

  ngOnDestroy() {
    if (this.themeObserver) this.themeObserver.disconnect();
    if (this.map) this.map.remove();
  }

  private initMap() {
    this.map = L.map('explorer-map', { zoomControl: false }).setView([-17.7833, -63.1821], 13);
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);
    
    const isLight = document.body.classList.contains('light-theme');
    const tileUrl = isLight 
      ? 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

    this.tileLayer = L.tileLayer(tileUrl, {
      attribution: '&copy; OpenStreetMap &copy; CARTO',
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

    this.workshopLayer.addTo(this.map);
  }

  private loadWorkshops(query: string = '') {
    let url = `${environment.apiUrl}/api/v1/workshops/active`;
    if (query) url += `?search=${encodeURIComponent(query)}`;
    
    this.http.get<any[]>(url).subscribe({
      next: (workshops) => {
        this.workshopLayer.clearLayers();
        workshops.forEach(ws => {
          const iconHtml = `<div style="font-size: 24px; text-shadow: 0 0 10px #00F2FF; animation: pulse 2s infinite;">🏪</div>`;
          const customIcon = L.divIcon({ html: iconHtml, className: 'custom-icon', iconSize: [30, 30], iconAnchor: [15, 15] });
          const marker = L.marker([ws.latitud, ws.longitud], { icon: customIcon });
          marker.bindPopup(`<b style="color:#00F2FF;">${ws.nombre}</b><br/>${ws.direccion}`);
          this.workshopLayer.addLayer(marker);
        });
      },
      error: (e) => console.error('Error fetching workshops', e)
    });
  }

  search() {
    if (!this.searchQuery.trim()) {
      this.searchResults = [];
      this.loadWorkshops('');
      return;
    }
    
    // 1. Search Workshops internally
    this.loadWorkshops(this.searchQuery);

    // 2. Geocoding via Nominatim for streets
    const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(this.searchQuery)}&format=json&limit=5`;
    this.http.get<any[]>(url).subscribe({
      next: (res) => { this.searchResults = res; },
      error: (e) => console.error('Error in Nominatim', e)
    });
  }

  goToLocation(latStr: string, lonStr: string) {
    if (this.map) {
      this.map.setView([parseFloat(latStr), parseFloat(lonStr)], 16);
      this.searchResults = []; // hide results
    }
  }

  toggleHeatmap() {
    if (this.showHeatmap) {
      if (this.heatData.length === 0) {
        this.http.get<any[]>(`${environment.apiUrl}/api/v1/incidents/heatmap`).subscribe({
          next: (data) => {
            // map intensity based on severidad (critico = higher weight)
            this.heatData = data.map(d => {
              const intensity = d.severidad === 'critico' ? 1.0 : (d.severidad === 'mayor' ? 0.7 : 0.4);
              return [d.lat, d.lng, intensity];
            });
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            this.heatLayer = L.heatLayer(this.heatData, { radius: 25, blur: 15, maxZoom: 14 }).addTo(this.map!);
          },
          error: (e) => console.error('Error fetching heatmap', e)
        });
      } else {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        this.heatLayer = L.heatLayer(this.heatData, { radius: 25, blur: 15, maxZoom: 14 }).addTo(this.map!);
      }
    } else {
      if (this.heatLayer && this.map) {
        this.map.removeLayer(this.heatLayer);
      }
    }
  }
}
