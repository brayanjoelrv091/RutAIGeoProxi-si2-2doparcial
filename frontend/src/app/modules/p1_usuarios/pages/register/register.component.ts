import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../auth.service';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, NgClass],
  templateUrl: './register.component.html',
  styleUrl: './register.component.css',
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  error = '';
  ok = false;
  loading = false;
  registeredRole = '';
  registeredEmail = '';
  showPassword = false;

  form = this.fb.nonNullable.group({
    nombre: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [
      Validators.required,
      Validators.minLength(8),
      Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$/)
    ]],
    rol: ['cliente', Validators.required]
  });

  submit(): void {
    if (this.form.invalid) return;
    const { nombre: name, email, password, rol } = this.form.getRawValue();
    this.error = '';
    this.ok = false;
    this.loading = true;
    this.auth.register(name, email, password, rol).subscribe({
      next: () => {
        this.ok = true;
        this.loading = false;
        this.registeredRole = rol;
        this.registeredEmail = email;
        // Ya NO redirigimos automáticamente al login.
        // Mostramos la pantalla de éxito con instrucciones.
      },
      error: (e) => {
        this.loading = false;
        this.error = e?.error?.detail ?? 'No se pudo registrar.';
      },
    });
  }
}
