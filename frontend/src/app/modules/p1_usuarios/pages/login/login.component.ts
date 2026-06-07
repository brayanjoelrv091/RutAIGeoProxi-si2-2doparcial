import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../auth.service';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, NgClass],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  error = '';
  successMessage = '';
  showPassword = false;

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['payment_success'] === 'true') {
        this.successMessage = '¡Pago procesado con éxito! Ya puedes iniciar sesión en tu cuenta SaaS.';
      } else if (params['payment_cancelled'] === 'true') {
        this.error = 'El pago fue cancelado. Puedes intentar registrarte nuevamente o iniciar sesión si tu cuenta se creó en modo gratuito.';
      }
    });
  }

  submit(): void {
    Object.values(this.form.controls).forEach(c => c.markAsTouched());
    if (this.form.invalid) return;
    const { email, password } = this.form.getRawValue();
    this.error = '';
    this.auth.login(email, password).subscribe({
      next: () => void this.router.navigate(['/home']),
      error: (err) => {
        if(err.error && err.error.detail) {
          this.error = err.error.detail;
        } else {
          this.error = 'Credenciales incorrectas o cuenta inactiva.';
        }
      },
    });
  }
}
