import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM_EMAIL", "noreply@fithub.lk")


def send_otp_email(to_email: str, name: str, otp: str) -> bool:
    if not SMTP_HOST or not SMTP_USER:
        logger.warning(f"[DEV] SMTP not configured. OTP for {to_email}: {otp}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Verify your Fithub account"
        msg["From"] = SMTP_FROM
        msg["To"] = to_email

        text = (
            f"Hi {name},\n\n"
            f"Your verification OTP is: {otp}\n\n"
            f"This OTP expires in 15 minutes.\n\n"
            f"Fithub Team"
        )
        html = f"""
        <html><body>
        <h2>Welcome to Fithub!</h2>
        <p>Hi {name},</p>
        <p>Your verification code is:</p>
        <h1 style="letter-spacing:8px;color:#1a73e8;">{otp}</h1>
        <p>This OTP expires in <strong>15 minutes</strong>.</p>
        <p>If you did not create this account, ignore this email.</p>
        <p>Fithub Team</p>
        </body></html>
        """

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())

        logger.info(f"OTP email sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send OTP email to {to_email}: {e}")
        return False
