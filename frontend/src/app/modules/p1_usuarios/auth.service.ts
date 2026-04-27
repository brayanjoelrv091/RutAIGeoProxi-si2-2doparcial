import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environment';

const TOKEN_KEY = 'access_token';
const ROLE_KEY = 'user_role';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface Vehicle {
  id: number;
  usuario_id: number;
  marca: string;
  modelo: string;
  placa: string;
  anio: number | null;
  color: string | null;
}

export interface Me {
  id: number;
  nombre: string;
  email: string;
  telefono: string | null;
  esta_activo: boolean;
  rol: string;
  permisos: Record<string, unknown> | null;
  vehiculos: Vehicle[];
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly base = environment.apiUrl;

  get token(): string | null {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  getUserRole(): string | null {
    return sessionStorage.getItem(ROLE_KEY);
  }

  isLoggedIn(): boolean {
    return !!this.token;
  }

  login(email: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${this.base}/auth/login`, { email, password })
      .pipe(
        tap((r) => {
          sessionStorage.setItem(TOKEN_KEY, r.access_token);
          try {
            const payload = JSON.parse(atob(r.access_token.split('.')[1]));
            sessionStorage.setItem(ROLE_KEY, payload.role || 'cliente');
          } catch {
            sessionStorage.setItem(ROLE_KEY, 'cliente');
          }
        })
      );
  }

  register(nombre: string, email: string, password: string, rol: string = 'cliente'): Observable<unknown> {
    return this.http.post(`${this.base}/auth/register`, { nombre, email, password, rol });
  }

  logout(): void {
    const t = this.token;
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(ROLE_KEY);
    if (!t) {
      void this.router.navigate(['/login']);
      return;
    }
    this.http.post(`${this.base}/auth/logout`, {}, { headers: { Authorization: `Bearer ${t}` } }).subscribe({
      next: () => void this.router.navigate(['/login']),
      error: () => void this.router.navigate(['/login']),
    });
  }

  me(): Observable<Me> {
    return this.http.get<Me>(`${this.base}/me`);
  }

  forgotPassword(email: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(`${this.base}/auth/forgot-password`, { email });
  }

  resetPassword(token: string, new_password: string): Observable<void> {
    return this.http.post<void>(`${this.base}/auth/reset-password`, { token, new_password });
  }

  changePassword(current_password: string, new_password: string): Observable<{ message: string }> {
    return this.http.patch<{ message: string }>(`${this.base}/me/password`, { current_password, new_password }, { headers: { Authorization: `Bearer ${this.token}` } });
  }

  // CU-05: Administración de usuarios y roles
  listUsers(): Observable<Me[]> {
    return this.http.get<Me[]>(`${this.base}/admin/users`);
  }

  updateUserRole(userId: number, rol: string): Observable<Me> {
    return this.http.patch<Me>(`${this.base}/admin/users/${userId}/role`, { rol });
  }

  updateUserPermissions(userId: number, permisos: Record<string, unknown>): Observable<Me> {
    return this.http.patch<Me>(`${this.base}/admin/users/${userId}/permissions`, { permisos });
  }

  addVehicle(body: { marca: string; modelo: string; placa: string; anio?: number | null; color?: string }): Observable<Vehicle> {
    return this.http.post<Vehicle>(`${this.base}/me/vehicles`, body);
  }

  deleteVehicle(id: number): Observable<unknown> {
    return this.http.delete(`${this.base}/me/vehicles/${id}`);
  }
}
