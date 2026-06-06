import { Component, OnInit, inject, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WorkshopService, Workshop, Technician } from '../../../../workshop.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-workshop-profile',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './workshop-profile.component.html',
  styleUrls: ['./workshop-profile.component.css']
})
export class WorkshopProfileComponent implements OnInit, OnDestroy {
  private readonly wsSvc = inject(WorkshopService);
  private readonly router = inject(Router);

  workshop: (Workshop & { tecnicos: Technician[] }) | null = null;
  loading = true;
  error = '';
  heartbeatInterval: any;

  ngOnInit() {
    this.loadProfile();
  }

  ngOnDestroy() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    // Opcional: avisar que nos desconectamos
    this.wsSvc.disconnect().subscribe();
  }

  loadProfile() {
    this.wsSvc.getMyProfile().subscribe({
      next: (profile) => {
        this.workshop = profile;
        this.loading = false;
        if (!this.heartbeatInterval && profile.estado_registro === 'completado') {
          this.startHeartbeat();
        }
      },
      error: (err: any) => {
        if (err.status === 404) {
          // No tiene taller registrado, mandarlo al wizard
          this.router.navigate(['/workshops/register']);
        } else {
          this.error = 'Error al cargar el perfil del taller';
        }
        this.loading = false;
      }
    });
  }

  startHeartbeat() {
    // Primer heartbeat inmediato
    this.wsSvc.heartbeat().subscribe();
    
    // Luego cada 60 segundos
    this.heartbeatInterval = setInterval(() => {
      this.wsSvc.heartbeat().subscribe({
        error: (e: any) => console.error('Heartbeat failed', e)
      });
    }, 60000);
  }

  toggleAvailability(techId: number, currentStatus: boolean) {
    this.wsSvc.toggleAvailability(techId, !currentStatus).subscribe({
      next: (updatedTech: Technician) => {
        if (this.workshop) {
          const t = this.workshop.tecnicos.find((x: Technician) => x.id === techId);
          if (t) t.esta_disponible = updatedTech.esta_disponible;
        }
      },
      error: (e: any) => console.error('Error toggling availability', e)
    });
  }

  goBack() {
    this.router.navigate(['/home']);
  }
}
