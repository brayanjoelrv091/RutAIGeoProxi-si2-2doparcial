import { Component, inject, OnInit } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { environment } from '../../../../environment';
import { AuthService } from '../../auth.service';

interface Tenant {
  id: number;
  nombre: string;
  slug: string;
  esta_activo: boolean;
  plan: string;
  creado_en: string;
}

@Component({
  selector: 'app-superadmin-saas',
  standalone: true,
  imports: [CommonModule, DatePipe],
  templateUrl: './superadmin-saas.component.html',
  styleUrls: ['./superadmin-saas.component.css'],
})
export class SuperadminSaasComponent implements OnInit {
  private readonly auth = inject(AuthService);
  
  tenants: Tenant[] = [];
  loading = true;
  error = '';

  ngOnInit(): void {
    this.fetchTenants();
  }

  async fetchTenants() {
    this.loading = true;
    try {
      const res = await fetch(`${environment.apiUrl}/admin/saas/tenants`, {
        headers: { Authorization: `Bearer ${this.auth.token}` }
      });
      if (res.ok) {
        this.tenants = await res.json();
      } else {
        this.error = 'No se pudieron cargar los tenants.';
      }
    } catch (e: any) {
      this.error = 'Error de conexión.';
    } finally {
      this.loading = false;
    }
  }

  async toggleStatus(tenant: Tenant) {
    const newStatus = !tenant.esta_activo;
    const confirmMsg = newStatus 
      ? `¿Estás seguro de ACTIVAR la suscripción de ${tenant.nombre}?` 
      : `¿Estás seguro de SUSPENDER a ${tenant.nombre}? El tenant y todos sus usuarios perderán acceso.`;
      
    if (!confirm(confirmMsg)) return;

    try {
      const res = await fetch(`${environment.apiUrl}/admin/saas/tenants/${tenant.id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${this.auth.token}`
        },
        body: JSON.stringify({ esta_activo: newStatus })
      });
      
      if (res.ok) {
        const updated = await res.json();
        const idx = this.tenants.findIndex(t => t.id === tenant.id);
        if (idx !== -1) {
          this.tenants[idx] = updated;
        }
      } else {
        alert('Error al actualizar el estado del tenant.');
      }
    } catch (e) {
      alert('Error de red al actualizar estado.');
    }
  }
}
