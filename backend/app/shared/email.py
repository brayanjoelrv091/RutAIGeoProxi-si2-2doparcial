import smtplib
from email.message import EmailMessage
from app.shared.config import settings

def send_reset_email(to_email: str, token: str):
    """
    Envía el correo de recuperación de contraseña vía Brevo (SMTP).
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP no configurado. No se enviará correo.")
        return

    # Usamos la URL local para el desarrollo (Angular)
    reset_url = f"http://localhost:4200/reset-password?token={token}"

    msg = EmailMessage()
    msg['Subject'] = "Recuperación de Contraseña - RutAIGeoProxi"
    msg['From'] = settings.FROM_EMAIL
    msg['To'] = to_email

    html_content = f"""
    <!DOCTYPE html>
    <html>
      <body style="margin: 0; padding: 0; background-color: #121212; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #E0E0E0;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #121212; padding: 40px 0;">
          <tr>
            <td align="center">
              <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #1E1E1E; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                <!-- Header -->
                <tr>
                  <td style="background-color: #2A2A2A; padding: 20px; text-align: center; border-bottom: 2px solid #00F2FF;">
                    <h1 style="color: #00F2FF; margin: 0; font-size: 24px; letter-spacing: 2px;">RUT<span style="color: #FFF;">AI</span>GEOPROXI</h1>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td style="padding: 40px 30px;">
                    <h2 style="color: #FFFFFF; font-size: 20px; margin-top: 0;">¡Hola!</h2>
                    <p style="color: #B0B0B0; font-size: 16px; line-height: 1.5; margin-bottom: 30px;">
                      Estás recibiendo este correo porque recibimos una solicitud de recuperación de contraseña para tu cuenta.
                    </p>
                    
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                      <tr>
                        <td align="center">
                          <a href="{reset_url}" style="display: inline-block; background-color: #00F2FF; color: #000000; font-weight: bold; font-size: 16px; text-decoration: none; padding: 14px 30px; border-radius: 4px;">
                            Restablecer Contraseña
                          </a>
                        </td>
                      </tr>
                    </table>

                    <p style="color: #B0B0B0; font-size: 16px; line-height: 1.5; margin-top: 30px;">
                      Este enlace de recuperación expirará en 60 minutos.
                    </p>
                    <p style="color: #B0B0B0; font-size: 16px; line-height: 1.5;">
                      Si no solicitaste un cambio de contraseña, no es necesario realizar ninguna acción.
                    </p>
                    <p style="color: #B0B0B0; font-size: 16px; line-height: 1.5; margin-top: 30px;">
                      Saludos,<br>
                      <strong style="color: #FFFFFF;">El equipo de RutAIGeoProxi</strong>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #333333; margin: 30px 0;">
                    
                    <p style="color: #777777; font-size: 13px; line-height: 1.5; word-break: break-all;">
                      Si tienes problemas para hacer clic en el botón "Restablecer Contraseña", copia y pega la siguiente URL en tu navegador web:<br>
                      <a href="{reset_url}" style="color: #0096FF; text-decoration: none;">{reset_url}</a>
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td style="background-color: #1A1A1A; padding: 20px; text-align: center;">
                    <p style="color: #777777; font-size: 12px; margin: 0;">
                      © 2026 RutAIGeoProxi. Todos los derechos reservados.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    msg.set_content(html_content, subtype='html')

    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
