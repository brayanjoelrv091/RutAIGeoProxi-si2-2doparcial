import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, fromEvent } from 'rxjs';
import { environment } from '../../../../environment';

export interface OfflineIncident {
  titulo: string;
  descripcion: string;
  latitud: number;
  longitud: number;
  direccion: string;
  idempotency_key: string;
}

@Injectable({
  providedIn: 'root'
})
export class OfflineService {
  private http = inject(HttpClient);
  private queueKey = 'offline_incidents_queue';
  
  public isOnline = new BehaviorSubject<boolean>(navigator.onLine);

  constructor() {
    this.initConnectivityListeners();
  }

  private initConnectivityListeners() {
    fromEvent(window, 'online').subscribe(() => {
      this.isOnline.next(true);
      this.syncOfflineQueue();
    });

    fromEvent(window, 'offline').subscribe(() => {
      this.isOnline.next(false);
    });
  }

  // Guardar en LocalStorage si no hay conexión
  enqueueIncident(incident: Omit<OfflineIncident, 'idempotency_key'>): string {
    const key = crypto.randomUUID();
    const offlineItem: OfflineIncident = {
      ...incident,
      idempotency_key: key
    };

    const queue = this.getQueue();
    queue.push(offlineItem);
    localStorage.setItem(this.queueKey, JSON.stringify(queue));
    
    return key;
  }

  getQueue(): OfflineIncident[] {
    const data = localStorage.getItem(this.queueKey);
    return data ? JSON.parse(data) : [];
  }

  clearQueue() {
    localStorage.removeItem(this.queueKey);
  }

  // Sincronizar hacia el backend cuando hay conexión
  syncOfflineQueue() {
    const queue = this.getQueue();
    if (queue.length === 0) return;

    this.http.post(`${environment.apiUrl}/realtime/incidents/offline-sync`, queue).subscribe({
      next: (res: any) => {
        console.log('Sincronización exitosa', res);
        this.clearQueue();
      },
      error: (err) => {
        console.error('Error sincronizando', err);
      }
    });
  }
}
