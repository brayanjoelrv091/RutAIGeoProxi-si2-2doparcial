import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-stripe-qr-modal',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './stripe-qr-modal.component.html',
  styleUrl: './stripe-qr-modal.component.css'
})
export class StripeQrModalComponent {
  @Input() planName: string = '';
  @Input() amount: number = 0;
  @Output() paymentSuccess = new EventEmitter<void>();
  @Output() cancel = new EventEmitter<void>();

  isProcessing = false;
  isSuccess = false;

  simulatePayment() {
    this.isProcessing = true;
    // Simulate a network delay for the payment
    setTimeout(() => {
      this.isProcessing = false;
      this.isSuccess = true;
      // Close modal after showing success message
      setTimeout(() => {
        this.paymentSuccess.emit();
      }, 1500);
    }, 2000);
  }

  close() {
    this.cancel.emit();
  }
}
