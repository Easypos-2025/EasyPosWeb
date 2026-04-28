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


def send_payment_received(company_name: str, plan_name: str, amount: float, admin_email: str):
    """Notifica a EasyPosWeb (interno) que un asociado registró un plan de pago."""
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h3 style="color:#f97316;">&#128179; Nuevo registro con plan de pago — EasyPosWeb</h3>
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:6px;font-weight:bold;width:140px;">Empresa:</td>
          <td style="padding:6px;">{company_name}</td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:6px;font-weight:bold;">Plan:</td>
          <td style="padding:6px;">{plan_name}</td></tr>
      <tr><td style="padding:6px;font-weight:bold;">Monto:</td>
          <td style="padding:6px;"><strong>${amount:,.0f}</strong></td></tr>
      <tr style="background:#f8f9fa;"><td style="padding:6px;font-weight:bold;">Admin email:</td>
          <td style="padding:6px;">{admin_email}</td></tr>
    </table>
    <p style="margin-top:16px;">
      Ingresa al panel SYSADMIN → <strong>Revisión de Pagos</strong> para procesar este pago.
    </p>
    </body></html>
    """
    _send(EMAIL_SENDER, f"[EasyPosWeb] Pago pendiente: {company_name} — {plan_name}", body)


def send_payment_approved(to_email: str, company_name: str, plan_name: str):
    """Notifica al asociado que su pago fue aprobado y su plan está activo."""
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h3 style="color:#10b981;">&#10003; ¡Pago aprobado! Tu plan está activo — EasyPosWeb</h3>
    <p>Hola,</p>
    <p>Nos complace informarte que el pago de activación de <strong>{company_name}</strong>
       ha sido <strong>aprobado exitosamente</strong>.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr style="background:#f0fdf4;"><td style="padding:10px;font-weight:bold;">Plan activado:</td>
          <td style="padding:10px;">{plan_name}</td></tr>
    </table>
    <p>Ya puedes ingresar a tu dashboard y comenzar a operar.</p>
    <p style="margin-top:16px;">
      <a href="{FRONTEND_URL}/login"
         style="background:#10b981;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
        Ir al dashboard
      </a>
    </p>
    <p style="color:#888;font-size:12px;margin-top:20px;">
      Si tienes preguntas, abre un ticket de soporte desde tu dashboard.
    </p>
    </body></html>
    """
    _send(to_email, f"¡Pago aprobado! Tu plan {plan_name} está activo — EasyPosWeb", body)


def send_payment_rejected(to_email: str, company_name: str, plan_name: str, reason: str):
    """Notifica al asociado que su comprobante fue rechazado con la razón."""
    body = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <h3 style="color:#ef4444;">&#9888; Comprobante de pago no aprobado — EasyPosWeb</h3>
    <p>Hola,</p>
    <p>Hemos revisado el comprobante de pago enviado para <strong>{company_name}</strong>
       (plan <strong>{plan_name}</strong>) y no pudimos aprobarlo por el siguiente motivo:</p>
    <div style="background:#fef2f2;border-left:4px solid #ef4444;padding:12px 16px;margin:16px 0;border-radius:4px;">
      <strong>Motivo:</strong> {reason}
    </div>
    <p>Por favor, ingresa a tu cuenta, revisa la información y vuelve a enviar tu comprobante.</p>
    <p style="margin-top:16px;">
      <a href="{FRONTEND_URL}/login"
         style="background:#2563eb;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
        Reintentar pago
      </a>
    </p>
    <p style="color:#888;font-size:12px;margin-top:20px;">
      Si crees que esto es un error, abre un ticket de soporte desde tu dashboard.
    </p>
    </body></html>
    """
    _send(to_email, "Comprobante rechazado — revisa tu pago en EasyPosWeb", body)


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