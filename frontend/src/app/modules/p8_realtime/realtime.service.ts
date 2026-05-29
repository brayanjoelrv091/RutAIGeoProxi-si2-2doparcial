import { Injectable, OnDestroy } from '@angular/core';
import { BehaviorSubject, Observable, Subject, timer } from 'rxjs';
import { environment } from '../../environment';

/**
 * P8 · CU-24 — Servicio WebSocket bidireccional con auto-reconnect.
 *
 * Características:
 *   - Reconexión automática con backoff exponencial
 *   - Heartbeat cada 30s para detección de desconexiones
 *   - Buffer de mensajes durante desconexión
 *   - Tipado de eventos (state_change, location_update, notification)
 */

export interface WSMessage {
  type: 'state_change' | 'location_update' | 'notification' | 'heartbeat' | 'ack' | 'error';
  incident_id?: number;
  [key: string]: any;
}

export type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting';

@Injectable({ providedIn: 'root' })
export class RealtimeService implements OnDestroy {

  // ── Estado de conexión observable ──
  private connectionState$ = new BehaviorSubject<ConnectionState>('disconnected');
  readonly state$ = this.connectionState$.asObservable();

  // ── Flujo de mensajes entrantes ──
  private messages$ = new Subject<WSMessage>();
  readonly onMessage$: Observable<WSMessage> = this.messages$.asObservable();

  // ── Internos ──
  private ws: WebSocket | null = null;
  private heartbeatInterval: any = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private currentChannel: string = '';
  private token: string = '';
  private pendingMessages: any[] = [];
  private destroyed = false;

  private get wsBaseUrl(): string {
    const httpUrl = environment.apiUrl || 'http://localhost:8000';
    return httpUrl.replace(/^http/, 'ws');
  }

  // ══════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ══════════════════════════════════════════════════════════════════

  /**
   * Conecta al canal WebSocket de un incidente específico.
   */
  connectToIncident(incidentId: number, token: string): void {
    this.token = token;
    this.currentChannel = `${this.wsBaseUrl}/realtime/ws/incidents/${incidentId}?token=${token}`;
    this.connect();
  }

  /**
   * Conecta al canal de notificaciones de un usuario.
   */
  connectToNotifications(userId: number, token: string): void {
    this.token = token;
    this.currentChannel = `${this.wsBaseUrl}/realtime/ws/notifications/${userId}?token=${token}`;
    this.connect();
  }

  /**
   * Envía un mensaje al WebSocket. Si no está conectado, lo encola.
   */
  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      this.pendingMessages.push(message);
    }
  }

  /**
   * Envía una actualización de ubicación GPS.
   */
  sendLocationUpdate(lat: number, lng: number, role: string = 'tecnico', extras?: any): void {
    this.send({
      type: 'location_update',
      lat,
      lng,
      role,
      ...extras,
    });
  }

  /**
   * Solicita un cambio de estado vía WebSocket.
   */
  sendStateChange(nuevoEstado: string, notas?: string): void {
    this.send({
      type: 'state_change',
      nuevo_estado: nuevoEstado,
      notas,
    });
  }

  /**
   * Desconecta y limpia recursos.
   */
  disconnect(): void {
    this.stopHeartbeat();
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.connectionState$.next('disconnected');
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    this.disconnect();
  }

  // ══════════════════════════════════════════════════════════════════
  // INTERNALS
  // ══════════════════════════════════════════════════════════════════

  private connect(): void {
    if (!this.currentChannel) return;

    this.connectionState$.next('connecting');

    try {
      this.ws = new WebSocket(this.currentChannel);
    } catch (err) {
      this.connectionState$.next('disconnected');
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.connectionState$.next('connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.flushPendingMessages();
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const data: WSMessage = JSON.parse(event.data);
        this.messages$.next(data);
      } catch {
        console.warn('[RealtimeService] Mensaje no parseable:', event.data);
      }
    };

    this.ws.onclose = (event: CloseEvent) => {
      this.stopHeartbeat();
      this.connectionState$.next('disconnected');

      if (!this.destroyed && event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      this.connectionState$.next('disconnected');
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts || this.destroyed) {
      console.error('[RealtimeService] Máximo de reconexiones alcanzado.');
      return;
    }

    this.connectionState$.next('reconnecting');
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;

    console.log(`[RealtimeService] Reconectando en ${delay}ms (intento ${this.reconnectAttempts})`);

    timer(delay).subscribe(() => {
      if (!this.destroyed) {
        this.connect();
      }
    });
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'heartbeat' });
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private flushPendingMessages(): void {
    const pending = [...this.pendingMessages];
    this.pendingMessages = [];
    pending.forEach(msg => this.send(msg));
  }
}
