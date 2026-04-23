import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def send_reset_email(to_email: str, token: str):
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
   
    subject = "Recuperación de contraseña"
    
    body = f"""
    <html>
    <body>
    <h3>Recuperación de contraseña</h3>

    <p>Hola,</p>

    <p>Haz clic en el siguiente enlace para restablecer tu contraseña:</p>

    <p>
        <a href="{reset_link}">
        Restablecer contraseña
        </a>
    </p>

    <p>Este enlace expirará en 30 minutos.</p>

    <p>Si no solicitaste este cambio, ignora este mensaje.</p>
    </body>
    </html>
    """


    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    #msg["From"] = EMAIL_SENDER
    msg["From"] = "Tu App EasyPosWeb <easypos.co@gmail.com>"
    msg["To"] = to_email

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()

        print("EMAIL ENVIADO A:", to_email)

    except Exception as e:
        print("ERROR EMAIL:", str(e))