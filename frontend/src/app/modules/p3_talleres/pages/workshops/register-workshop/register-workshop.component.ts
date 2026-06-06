import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { WorkshopService, Technician } from '../../../workshop.service';

@Component({
  selector: 'app-register-workshop',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './register-workshop.component.html',
  styleUrl: './register-workshop.component.css',
})
export class RegisterWorkshopComponent implements OnInit {
  private readonly wsSvc = inject(WorkshopService);
  private readonly fb = inject(FormBuilder);
  public readonly router = inject(Router);

  workshopForm = this.fb.nonNullable.group({
    nombre: ['', [Validators.required, Validators.minLength(2)]],
    direccion: ['', [Validators.required, Validators.minLength(5)]],
    latitud: [0, Validators.required],
    longitud: [0, Validators.required],
    telefono: [''],
    email: [''],
    especialidades: [''],
  });

  techForm = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    telefono: [''],
    especialidad: [''],
  });

  createdWorkshopId: number | null = null;
  technicians: Technician[] = [];
  error = '';
  success = '';
  locLoading = false;
  checkingProfile = true;

  ngOnInit() {
    this.checkExistingProfile();
  }

  checkExistingProfile() {
    this.wsSvc.getMyProfile().subscribe({
      next: (profile) => {
        if (profile) {
          if ((profile as any).estado_registro === 'completado') {
            this.router.navigate(['/workshops/profile']);
            return;
          } else {
            // Retomar donde quedó
            this.createdWorkshopId = profile.id;
            this.technicians = profile.tecnicos || [];
            this.success = 'Retomando registro del taller...';
          }
        }
        this.checkingProfile = false;
      },
      error: (e) => {
        // No tiene taller (404), continuar normal
        this.checkingProfile = false;
      }
    });
  }

  detectLocation(): void {
    if (!navigator.geolocation) return;
    this.locLoading = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.workshopForm.patchValue({ latitud: pos.coords.latitude, longitud: pos.coords.longitude });
        this.locLoading = false;
      },
      () => (this.locLoading = false),
      { enableHighAccuracy: true }
    );
  }

  registerWorkshop(): void {
    if (this.workshopForm.invalid) return;
    this.error = '';
    const v = this.workshopForm.getRawValue();
    const specs = v.especialidades ? v.especialidades.split(',').map((s: string) => s.trim()).filter(Boolean) : undefined;
    this.wsSvc.registerWorkshop({
      nombre: v.nombre, direccion: v.direccion, latitud: v.latitud, longitud: v.longitud,
      telefono: v.telefono || undefined, email: v.email || undefined, especialidades: specs,
    }).subscribe({
      next: (ws) => {
        this.createdWorkshopId = ws.id;
        this.success = `Taller "${ws.nombre}" registrado correctamente. Ahora agregue a sus técnicos.`;
      },
      error: (e) => (this.error = e?.error?.detail || 'Error al registrar taller'),
    });
  }

  addTechnician(): void {
    if (!this.createdWorkshopId || this.techForm.invalid) return;
    const v = this.techForm.getRawValue();
    this.wsSvc.addTechnician(this.createdWorkshopId, {
      nombre: v.nombre, telefono: v.telefono || undefined, especialidad: v.especialidad || undefined,
    }).subscribe({
      next: (t) => {
        this.technicians.push(t);
        this.techForm.reset({ nombre: '', telefono: '', especialidad: '' });
      },
      error: (e) => (this.error = e?.error?.detail || 'Error al agregar técnico'),
    });
  }

  finishRegistration(): void {
    this.wsSvc.completeRegistration().subscribe({
      next: () => {
        this.router.navigate(['/workshops/profile']);
      },
      error: (e) => (this.error = e?.error?.detail || 'Error al completar el registro'),
    });
  }
}

