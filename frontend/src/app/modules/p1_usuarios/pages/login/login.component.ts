import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
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

  error = '';
  showPassword = false;

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

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
