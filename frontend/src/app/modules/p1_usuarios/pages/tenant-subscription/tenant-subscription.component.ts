import { Component, OnInit, inject } from '@angular/core';
import { Router, ActivatedRoute, RouterLink } from '@angular/router';
import { AuthService, Me } from '../../auth.service';
import { StripeQrModalComponent } from '../../../../shared/components/stripe-qr-modal/stripe-qr-modal.component';
import { UpperCasePipe } from '@angular/common';

@Component({
  selector: 'app-tenant-subscription',
  standalone: true,
  imports: [RouterLink, StripeQrModalComponent, UpperCasePipe],
  templateUrl: './tenant-subscription.component.html',
  styleUrl: './tenant-subscription.component.css'
})
export class TenantSubscriptionComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  me: Me | null = null;
  loading = true;

  showPaymentMethodModal = false;
  showStripeModal = false; // El modal de QR que en realidad simula QR
  upgradePlanName = '';
  upgradeAmount = 0;

  ngOnInit(): void {
    this.auth.me().subscribe({
      next: (m) => {
        this.me = m;
        this.loading = false;
        this.checkStripeRedirect();
      },
      error: () => {
        this.router.navigate(['/login']);
      }
    });
  }

  checkStripeRedirect() {
    this.route.queryParams.subscribe(params => {
      if (params['payment_success'] === 'true') {
        // Asumimos que guardamos en sessionStorage o localstorage el plan que estábamos comprando
        // Para la demo, podemos inferir que si viene de stripe, el plan cambió, o simplemente mostrar éxito.
        // Pero idealmente llamamos a confirmUpgradeTenant.
        const planPendiente = sessionStorage.getItem('pending_plan') || 'profesional';
        const montoPendiente = parseFloat(sessionStorage.getItem('pending_amount') || '29.00');
        
        this.auth.confirmUpgradeTenant(planPendiente, 'tarjeta', montoPendiente).subscribe({
          next: () => {
            alert('¡Pago verificado y plan actualizado exitosamente!');
            // Limpiamos la URL
            this.router.navigate([], { replaceUrl: true });
            // Recargamos el perfil local
            if (this.me) {
              this.me.tenant_plan = planPendiente;
            }
            sessionStorage.removeItem('pending_plan');
            sessionStorage.removeItem('pending_amount');
          },
          error: (e: any) => {
            alert('Error confirmando el pago: ' + e.message);
          }
        });
      }
    });
  }

  openUpgradeModal(plan: string) {
    if (this.me?.tenant_plan === plan) return;
    this.upgradePlanName = plan;
    this.upgradeAmount = plan === 'profesional' ? 29 : (plan === 'empresarial' ? 99 : 0);
    this.showPaymentMethodModal = true;
  }

  selectPaymentMethod(method: 'qr' | 'tarjeta') {
    this.showPaymentMethodModal = false;
    
    if (method === 'qr') {
      this.showStripeModal = true; // El modal de QR
    } else {
      if (!confirm(`¿Está seguro de querer cambiar al plan ${this.upgradePlanName.toUpperCase()} con Tarjeta? Será redirigido a Stripe.`)) return;
      
      // Guardar el plan pendiente para confirmarlo luego
      sessionStorage.setItem('pending_plan', this.upgradePlanName);
      sessionStorage.setItem('pending_amount', this.upgradeAmount.toString());

      this.auth.upgradeTenantPlan(this.upgradePlanName, 'tarjeta').subscribe({
        next: (res: any) => {
          if (res && res.checkout_url) {
            window.location.href = res.checkout_url;
          } else {
            alert('No se generó la URL de Stripe.');
          }
        },
        error: (e: any) => {
          alert('Error al generar sesión de pago: ' + (e.error?.detail || 'Desconocido'));
        }
      });
    }
  }

  onUpgradePaymentSuccess() {
    this.showStripeModal = false;
    // Pago por QR exitoso (simulado por el modal)
    this.auth.confirmUpgradeTenant(this.upgradePlanName, 'qr', this.upgradeAmount).subscribe({
      next: () => {
        alert('¡Pago por QR verificado y plan actualizado exitosamente!');
        if (this.me) {
          this.me.tenant_plan = this.upgradePlanName;
        }
      },
        error: (e: any) => {
        alert('Error confirmando el pago: ' + (e.error?.detail || 'Desconocido'));
      }
    });
  }

  onUpgradePaymentCancel() {
    this.showStripeModal = false;
  }
}
