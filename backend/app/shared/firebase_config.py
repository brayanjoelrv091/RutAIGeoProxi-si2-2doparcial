import firebase_admin
from firebase_admin import credentials, messaging
import os
import logging

logger = logging.getLogger(__name__)

# Ruta al archivo de credenciales (firebase-key.json)
# Se asume que está en la raíz de la carpeta backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SERVICE_ACCOUNT_KEY_PATH = os.path.join(BASE_DIR, "firebase-key.json")

def init_firebase():
    """Inicializa el SDK de Firebase Admin"""
    if not firebase_admin._apps:
        try:
            if os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
                cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("🔥 Firebase Admin SDK inicializado correctamente.")
            else:
                logger.error(f"❌ Error: No se encontró el archivo {SERVICE_ACCOUNT_KEY_PATH}")
        except Exception as e:
            logger.error(f"❌ Error al inicializar Firebase: {e}")

def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Envía una notificación push a un dispositivo específico a través de su token FCM.
    """
    if not fcm_token:
        return False
        
    try:
        # Si no se ha inicializado, intentar hacerlo
        if not firebase_admin._apps:
            init_firebase()
            
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
        )
        
        response = messaging.send(message)
        logger.info(f"✅ Notificación enviada con éxito: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación FCM: {e}")
        return False
