import stripe
import json
from app.shared.config import settings

# Configurar API Key
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeGateway:
    @staticmethod
    def process_payment(amount: float, currency: str, source: str = "tok_visa") -> dict:
        """
        Procesa un pago con Stripe. 
        Por simplicidad en la prueba, usamos un token de prueba (tok_visa) por defecto.
        """
        try:
            # Convertir monto a centavos
            amount_cents = int(amount * 100)
            
            charge = stripe.Charge.create(
                amount=amount_cents,
                currency=currency,
                source=source,
                description="Pago por servicio en RutAIGeoProxi"
            )
            
            return {
                "success": charge.status == "succeeded",
                "transaction_id": charge.id,
                "raw_response": json.dumps(charge)
            }
        except stripe.error.StripeError as e:
            return {
                "success": False,
                "transaction_id": None,
                "raw_response": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "transaction_id": None,
                "raw_response": str(e)
            }
