import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { environment } from '../../../../../environments/environment';
import { AuthService } from '../../auth.service';

interface User {
  id: number;
  nombre: string;
  email: string;
  rol: string;
  permisos: any;
}

interface Bitacora {
  id: number;
  usuario_id: number;
  rol: string;
  accion: string;
  ip: string;
  creado_en: string;
}

@Component({
  selector: 'app-admin-users',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-users.component.html',
  styleUrls: ['./admin-users.component.css'],
})
export class AdminUsersComponent implements OnInit {
  private readonly auth = inject(AuthService);

  users: User[] = [];
  bitacora: Bitacora[] = [];
  loading = true;
  error = '';
  editingUser: User | null = null;
  newPermissionsStr = '';

  roles = ['admin', 'taller', 'cliente'];

  ngOnInit(): void {
    this.loadData();
  }

  async loadData() {
    this.loading = true;
    this.error = '';
    try {
      await Promise.all([this.fetchUsers(), this.fetchAudit()]);
    } catch (e: any) {
      this.error = 'Error de conexión con la red principal.';
    } finally {
      this.loading = false;
    }
  }

  async fetchUsers() {
    const token = this.auth.getToken();
    const res = await fetch(`${environment.apiUrl}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      this.users = await res.json();
    }
  }

  async fetchAudit() {
    const token = this.auth.getToken();
    const res = await fetch(`${environment.apiUrl}/admin/audit`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      this.bitacora = await res.json();
    }
  }

  loadUsers(): void {
    this.loadData();
  }

  changeRole(user: User, newRole: string): void {
    if (user.rol === newRole) return;
    
    this.auth.updateUserRole(user.id, newRole).subscribe({
      next: (updated) => {
        const idx = this.users.findIndex((u) => u.id === user.id);
        if (idx !== -1) this.users[idx] = updated;
      },
      error: (err) => {
        alert(err.error?.detail || 'Error al actualizar rol');
      },
    });
  }

  openPermissions(user: User): void {
    this.editingUser = user;
    this.newPermissionsStr = JSON.stringify(user.permisos || {}, null, 2);
  }

  savePermissions(): void {
    if (!this.editingUser) return;
    
    try {
      const perms = JSON.parse(this.newPermissionsStr);
      this.auth.updateUserPermissions(this.editingUser.id, perms).subscribe({
        next: (updated) => {
          const idx = this.users.findIndex((u) => u.id === this.editingUser!.id);
          if (idx !== -1) this.users[idx] = updated;
          this.editingUser = null;
        },
        error: (err) => {
          alert('Error al guardar permisos');
        },
      });
    } catch (e) {
      alert('JSON de permisos inválido');
    }
  }
}
