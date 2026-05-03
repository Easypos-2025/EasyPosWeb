"""
Email Service — EasyPosWeb
Estrategia:
  - Si RESEND_API_KEY está configurada → usa Resend HTTP API (sin SMTP, sin bloqueos de puerto).
  - Si no → fallback a SMTP (útil en desarrollo local).

DigitalOcean bloquea puertos SMTP salientes (25/587) en VPS nuevos;
por eso en producción se usa Resend (HTTPS puerto 443).
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

SMTP_SERVER    = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5173")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_ADDRESS   = os.getenv("EMAIL_FROM", "EasyPosWeb <noreply@easyposweb.com>")

SMTP_TIMEOUT = 15

# Defaults usados cuando la DB no está disponible
_FOOTER_DEFAULTS = {
    "email_footer_legal_name":    "EasyPosWeb SAS",
    "email_footer_nit":           "900.123.456-7",
    "email_footer_tagline":       "Tu negocio, en línea. Sin complicaciones.",
    "email_footer_website":       "https://easyposweb.com",
    "email_footer_support_email": "soporte@easyposweb.com",
    "email_footer_phone":         "",
    "email_footer_address":       "Colombia",
}


def _get_footer_config() -> dict:
    """Lee la configuración del pie de email desde system_config. Usa defaults si falla."""
    try:
        from app.database import SessionLocal
        from app.models.system_config_model import SystemConfig
        db = SessionLocal()
        try:
            rows = db.query(SystemConfig).filter(
                SystemConfig.config_key.in_(list(_FOOTER_DEFAULTS.keys())),
                SystemConfig.is_active == True,
            ).all()
            cfg = dict(_FOOTER_DEFAULTS)
            for r in rows:
                cfg[r.config_key] = r.config_value
            return cfg
        finally:
            db.close()
    except Exception:
        return dict(_FOOTER_DEFAULTS)


def _build_footer(cfg: dict | None = None) -> str:
    """Genera el bloque HTML del pie de página para todos los emails."""
    if cfg is None:
        cfg = _get_footer_config()

    legal_name    = cfg.get("email_footer_legal_name",    _FOOTER_DEFAULTS["email_footer_legal_name"])
    nit           = cfg.get("email_footer_nit",           _FOOTER_DEFAULTS["email_footer_nit"])
    tagline       = cfg.get("email_footer_tagline",       _FOOTER_DEFAULTS["email_footer_tagline"])
    website       = cfg.get("email_footer_website",       _FOOTER_DEFAULTS["email_footer_website"])
    support_email = cfg.get("email_footer_support_email", _FOOTER_DEFAULTS["email_footer_support_email"])
    phone         = cfg.get("email_footer_phone",         _FOOTER_DEFAULTS["email_footer_phone"])
    address       = cfg.get("email_footer_address",       _FOOTER_DEFAULTS["email_footer_address"])

    phone_row = (
        f'<span style="color:#64748b;">&#128222; {phone}</span>&nbsp;&nbsp;'
        if phone else ""
    )

    return f"""
<div style="margin-top:32px;padding-top:20px;border-top:1px solid #e2e8f0;
            max-width:600px;font-family:Arial,sans-serif;">

  <!-- Logotipo textual tricolor -->
  <p style="margin:0 0 4px;font-size:18px;font-weight:800;letter-spacing:-0.5px;line-height:1;">
    <span style="color:#2563eb;">Easy</span><span style="color:#f59e0b;">Pos</span><span style="color:#10b981;">Web</span>
  </p>
  <p style="margin:0 0 12px;font-size:12px;color:#64748b;">{tagline}</p>

  <!-- Datos de contacto -->
  <p style="margin:0 0 6px;font-size:12px;color:#64748b;">
    {phone_row}
    <span style="color:#64748b;">&#9993; <a href="mailto:{support_email}"
      style="color:#2563eb;text-decoration:none;">{support_email}</a></span>&nbsp;&nbsp;
    <span style="color:#64748b;">&#127760; <a href="{website}"
      style="color:#2563eb;text-decoration:none;">{website}</a></span>
  </p>

  <!-- Aviso no-reply -->
  <p style="margin:10px 0 6px;font-size:11px;color:#94a3b8;">
    Este correo fue generado automáticamente. Por favor no respondas a este mensaje.
    Si necesitas ayuda, escríbenos a
    <a href="mailto:{support_email}" style="color:#2563eb;">{support_email}</a>.
  </p>

  <!-- Datos legales -->
  <p style="margin:0;font-size:10px;color:#cbd5e1;">
    &copy; {__import__('datetime').date.today().year} {legal_name}
    &nbsp;&middot;&nbsp; NIT {nit}
    &nbsp;&middot;&nbsp; {address}
  </p>

</div>
"""


def _wrap_email(title_color: str, content_html: str) -> str:
    """Envuelve el contenido en un layout de email consistente con pie incluido."""
    footer = _build_footer()
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;color:#1e293b;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f1f5f9;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        <tr><td style="background:#ffffff;border-radius:12px;
                       padding:32px 36px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          {content_html}
          {footer}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send(to: str, subject: str, body_html: str):
    """Envía un correo usando Resend API (producción) o SMTP (desarrollo)."""
    if RESEND_API_KEY:
        _send_resend(to, subject, body_html)
    else:
        _send_smtp(to, subject, body_html)


def _send_resend(to: str, subject: str, body_html: str):
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from":    FROM_ADDRESS,
            "to":      [to],
            "subject": subject,
            "html":    body_html,
        })
        print(f"RESEND EMAIL ENVIADO A: {to}")
    except Exception as e:
        print(f"RESEND ERROR: {e}")


def _send_smtp(to: str, subject: str, body_html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"EasyPosWeb <{EMAIL_SENDER}>"
    msg["To"]      = to
    msg.attach(MIMEText(body_html, "html"))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to, msg.as_string())
        server.quit()
        print(f"SMTP EMAIL ENVIADO A: {to}")
    except Exception as e:
        print(f"SMTP ERROR: {e}")


# ── Funciones de negocio ──────────────────────────────────────────────────────

def send_reset_email(to_email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    content = f"""
    <h2 style="margin:0 0 16px;color:#2563eb;font-size:20px;">
      &#128274; Recuperación de contraseña
    </h2>
    <p style="margin:0 0 12px;">Hola,</p>
    <p style="margin:0 0 20px;">
      Recibimos una solicitud para restablecer la contraseña de tu cuenta.
      Haz clic en el botón para continuar:
    </p>
    <p style="margin:0 0 24px;">
      <a href="{reset_link}"
         style="display:inline-block;background:#2563eb;color:#ffffff;
                padding:12px 28px;border-radius:8px;text-decoration:none;
                font-weight:700;font-size:14px;">
        Restablecer contraseña
      </a>
    </p>
    <p style="margin:0;font-size:12px;color:#64748b;">
      &#9201; Este enlace expirará en <strong>60 minutos</strong>.<br>
      Si no solicitaste este cambio, ignora este mensaje — tu contraseña no cambiará.
    </p>
    """
    _send(to_email, "Recuperación de contraseña — EasyPosWeb", _wrap_email("#2563eb", content))


def send_payment_received(company_name: str, plan_name: str, amount: float, admin_email: str):
    """Notifica internamente que un asociado registró un plan de pago."""
    content = f"""
    <h2 style="margin:0 0 16px;color:#f97316;font-size:20px;">
      &#128179; Nuevo registro con plan de pago
    </h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;font-size:14px;">
      <tr>
        <td style="padding:9px 12px;font-weight:700;background:#f8fafc;
                   width:140px;border-radius:6px 0 0 0;">Empresa</td>
        <td style="padding:9px 12px;background:#f8fafc;border-radius:0 6px 0 0;">{company_name}</td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;">Plan</td>
        <td style="padding:9px 12px;">{plan_name}</td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;background:#f8fafc;">Monto</td>
        <td style="padding:9px 12px;background:#f8fafc;font-weight:700;color:#f97316;">
          ${amount:,.0f} COP
        </td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;">Email admin</td>
        <td style="padding:9px 12px;">{admin_email}</td>
      </tr>
    </table>
    <div style="background:#fff7ed;border-left:4px solid #f97316;
                padding:12px 16px;border-radius:0 6px 6px 0;font-size:13px;">
      Ingresa al panel SYSADMIN &rarr; <strong>Revisión de Pagos</strong>
      para procesar este pago.
    </div>
    """
    _send(
        EMAIL_SENDER or "easypos.co@gmail.com",
        f"[EasyPosWeb] Pago pendiente: {company_name} — {plan_name}",
        _wrap_email("#f97316", content),
    )


def send_payment_approved(to_email: str, company_name: str, plan_name: str):
    """Notifica al asociado que su pago fue aprobado."""
    content = f"""
    <h2 style="margin:0 0 16px;color:#10b981;font-size:20px;">
      &#10003; ¡Pago aprobado! Tu plan está activo
    </h2>
    <p style="margin:0 0 12px;">Hola,</p>
    <p style="margin:0 0 20px;">
      El pago de activación de <strong>{company_name}</strong> fue
      <strong style="color:#10b981;">aprobado exitosamente</strong>.
    </p>
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:14px;">
      <tr>
        <td style="padding:12px 16px;background:#f0fdf4;border-radius:8px;
                   font-weight:700;color:#065f46;text-align:center;">
          &#127941; Plan activado: <span style="font-size:16px;">{plan_name}</span>
        </td>
      </tr>
    </table>
    <p style="margin:0 0 20px;">
      Ya puedes ingresar a tu dashboard y comenzar a operar sin restricciones.
    </p>
    <p style="margin:0 0 12px;">
      <a href="{FRONTEND_URL}/login"
         style="display:inline-block;background:#10b981;color:#ffffff;
                padding:12px 28px;border-radius:8px;text-decoration:none;
                font-weight:700;font-size:14px;">
        Ir al dashboard &#8594;
      </a>
    </p>
    """
    _send(
        to_email,
        f"¡Pago aprobado! Tu plan {plan_name} está activo — EasyPosWeb",
        _wrap_email("#10b981", content),
    )


def send_payment_rejected(to_email: str, company_name: str, plan_name: str, reason: str):
    """Notifica al asociado que su comprobante fue rechazado con la razón."""
    content = f"""
    <h2 style="margin:0 0 16px;color:#ef4444;font-size:20px;">
      &#9888; Comprobante no aprobado
    </h2>
    <p style="margin:0 0 12px;">Hola,</p>
    <p style="margin:0 0 16px;">
      Revisamos el comprobante de <strong>{company_name}</strong>
      (plan <strong>{plan_name}</strong>) y no pudimos aprobarlo por el siguiente motivo:
    </p>
    <div style="background:#fef2f2;border-left:4px solid #ef4444;
                padding:12px 16px;border-radius:0 6px 6px 0;
                margin-bottom:20px;font-size:14px;">
      <strong>Motivo:</strong> {reason}
    </div>
    <p style="margin:0 0 20px;font-size:14px;">
      Por favor ingresa a tu cuenta, verifica la información y vuelve a enviar tu comprobante.
    </p>
    <p style="margin:0;">
      <a href="{FRONTEND_URL}/login"
         style="display:inline-block;background:#2563eb;color:#ffffff;
                padding:12px 28px;border-radius:8px;text-decoration:none;
                font-weight:700;font-size:14px;">
        Reintentar pago &#8594;
      </a>
    </p>
    """
    _send(
        to_email,
        "Comprobante rechazado — revisa tu pago en EasyPosWeb",
        _wrap_email("#ef4444", content),
    )


def send_contact_email(name: str, email: str, message: str,
                       phone: str = "", company: str = ""):
    content = f"""
    <h2 style="margin:0 0 16px;color:#2563eb;font-size:20px;">
      &#128235; Nuevo mensaje de contacto
    </h2>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;font-size:14px;">
      <tr>
        <td style="padding:9px 12px;font-weight:700;background:#f8fafc;width:120px;">Nombre</td>
        <td style="padding:9px 12px;background:#f8fafc;">{name}</td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;">Email</td>
        <td style="padding:9px 12px;">{email}</td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;background:#f8fafc;">Teléfono</td>
        <td style="padding:9px 12px;background:#f8fafc;">{phone or "—"}</td>
      </tr>
      <tr>
        <td style="padding:9px 12px;font-weight:700;">Empresa</td>
        <td style="padding:9px 12px;">{company or "—"}</td>
      </tr>
    </table>
    <h4 style="margin:0 0 8px;font-size:14px;color:#374151;">Mensaje:</h4>
    <div style="background:#f8fafc;padding:14px 16px;border-radius:8px;
                font-size:14px;line-height:1.6;white-space:pre-wrap;">{message}</div>
    """
    _send(
        EMAIL_SENDER or "easypos.co@gmail.com",
        f"Contacto Web: {name} — {company or email}",
        _wrap_email("#2563eb", content),
    )
