import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

SMTP_SERVER   = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER  = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FRONTEND_URL  = os.getenv("FRONTEND_URL", "http://localhost:5173")
DISPLAY_NAME  = "EasyPosWeb <easypos.co@gmail.com>"


def _send(to: str, subject: str, body_html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = DISPLAY_NAME
    msg["To"]      = to
    msg.attach(MIMEText(body_html, "html"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to, msg.as_string())
        server.quit()
        print(f"EMAIL ENVIADO A: {to}")
    except Exception as e:
        print(f"ERROR EMAIL: {e}")


def send_reset_email(to_email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h3 style="color:#0d6efd;">Recuperación de contraseña — EasyPosWeb</h3>
    <p>Hola,</p>
    <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>
    <p><a href="{reset_link}" style="background:#0d6efd;color:#fff;padding:10px 20px;
       border-radius:5px;text-decoration:none;">Restablecer contraseña</a></p>
    <p style="color:#888;font-size:12px;">Este enlace expirará en 30 minutos.
    Si no solicitaste este cambio, ignora este mensaje.</p>
    </body></html>
    """
    _send(to_email, "Recuperación de contraseña — EasyPosWeb", body)


def send_contact_email(name: str, email: str, message: str,
                       phone: str = "", company: str = ""):
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h3 style="color:#0d6efd;">Nuevo mensaje de contacto — EasyPosWeb</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:6px;font-weight:bold;width:120px;">Nombre:</td>
          <td style="padding:6px;">{name}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:6px;font-weight:bold;">Email:</td>
          <td style="padding:6px;">{email}</td></tr>
      <tr><td style="padding:6px;font-weight:bold;">Teléfono:</td>
          <td style="padding:6px;">{phone or "—"}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:6px;font-weight:bold;">Empresa:</td>
          <td style="padding:6px;">{company or "—"}</td></tr>
    </table>
    <h4 style="margin-top:16px;">Mensaje:</h4>
    <p style="background:#f8f9fa;padding:12px;border-radius:6px;">{message}</p>
    </body></html>
    """
    _send(EMAIL_SENDER, f"Contacto Web: {name} — {company or email}", body)