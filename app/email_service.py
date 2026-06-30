"""
E-Mail-Versand via SMTP (aiosmtplib).
"""
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def sende_email(
    empfaenger: str,
    betreff: str,
    html_body: str,
    text_body: Optional[str] = None,
) -> bool:
    """Sendet eine E-Mail. Gibt True bei Erfolg zurück."""
    if not settings.smtp_configured:
        logger.warning("SMTP nicht konfiguriert – E-Mail wird nicht gesendet.")
        logger.info(f"[DEV] An: {empfaenger} | Betreff: {betreff}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = betreff
    msg["From"] = settings.smtp_from
    msg["To"] = empfaenger

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=settings.smtp_tls,
        )
        logger.info(f"E-Mail gesendet an {empfaenger}")
        return True
    except Exception as e:
        logger.error(f"E-Mail-Fehler an {empfaenger}: {e}")
        return False


async def sende_einladung(email: str, token: str, eingeladen_von: str) -> bool:
    einladungslink = f"{settings.app_name}"  # wird zur Laufzeit mit base_url ersetzt
    # Der Link wird im Router zusammengebaut, hier nur die Template-Logik
    betreff = f"Einladung zur {settings.app_name}"
    html = f"""
    <html><body>
    <h2>Einladung</h2>
    <p>Sie wurden von <strong>{eingeladen_von}</strong> zur <strong>{settings.app_name}</strong> eingeladen.</p>
    <p>Klicken Sie auf den folgenden Link, um Ihr Konto einzurichten:</p>
    <p><a href="{token}">Einladung annehmen</a></p>
    <p>Dieser Link ist 7 Tage gültig.</p>
    </body></html>
    """
    return await sende_email(email, betreff, html)
