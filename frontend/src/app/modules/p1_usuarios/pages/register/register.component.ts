import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../auth.service';
import { NgClass, UpperCasePipe } from '@angular/common';
import { StripeQrModalComponent } from '../../../../shared/components/stripe-qr-modal/stripe-qr-modal.component';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, NgClass, UpperCasePipe, StripeQrModalComponent],
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
  
  // Stripe modal state
  showStripeModal = false;
  stripePlanName = '';
  stripeAmount = 0;

  form = this.fb.group({
    nombre: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    password: ['', [
      Validators.required,
      Validators.minLength(8),
      Validators.pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d\w\W]{8,}$/)
    ]],
    rol: ['cliente', Validators.required],
    tenant_name: [''],
    plan: [''],
    metodo_pago: ['tarjeta']
  });

  ngOnInit() {
    this.form.get('rol')?.valueChanges.subscribe(rol => {
      if (rol === 'admin') {
        this.form.get('tenant_name')?.setValidators([Validators.required]);
        this.form.get('plan')?.setValidators([Validators.required]);
        this.form.get('plan')?.setValue('gratis');
      } else {
        this.form.get('tenant_name')?.clearValidators();
        this.form.get('plan')?.clearValidators();
      }
      this.form.get('tenant_name')?.updateValueAndValidity();
      this.form.get('plan')?.updateValueAndValidity();
    });
  }

  showStripeModal = false;
  stripePlanName = '';
  stripeAmount = 0;

  submit(): void {
    if (this.form.invalid) return;
    
    const vals = this.form.getRawValue();
    if (vals.plan !== 'gratis' && vals.metodo_pago === 'qr') {
      this.stripePlanName = vals.plan!;
      this.stripeAmount = vals.plan === 'profesional' ? 29 : 99;
      this.showStripeModal = true;
    } else {
      this.executeRegistration();
    }
  }

  executeRegistration(): void {
    const vals = this.form.getRawValue();
    const name = vals.nombre!;
    const email = vals.email!;
    const password = vals.password!;
    const rol = vals.rol!;
    const tenant_name = vals.tenant_name || undefined;
    const plan = vals.plan || undefined;
    const metodo_pago = vals.metodo_pago || undefined;

    this.error = '';
    this.ok = false;
    this.loading = true;
    this.auth.register(name, email, password, rol, tenant_name, plan, metodo_pago).subscribe({
      next: (res) => {
        if (res.checkout_url) {
          window.location.href = res.checkout_url;
          return;
        }
        this.ok = true;
        this.loading = false;
        this.registeredRole = rol;
        this.registeredEmail = email;
      },
      error: (e) => {
        this.loading = false;
        this.error = e?.error?.detail ?? 'No se pudo registrar.';
      },
    });
  }

  onPaymentSuccess() {
    this.showStripeModal = false;
    this.executeRegistration();
  }

  onPaymentCancel() {
    this.showStripeModal = false;
  }
}
