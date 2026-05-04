"""
Gmail SMTP helpers for account verification and password reset emails.
Requires env vars: GMAIL_USER, GMAIL_APP_PASSWORD
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_GMAIL_USER = os.getenv('GMAIL_USER', '')
_GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

_APP_NAME = "Ecosystem Valuation Engine"
_APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://eve-valuation-engine-1025191764754.us-central1.run.app')


def _send(to_email: str, subject: str, html_body: str) -> bool:
    if not _GMAIL_USER or not _GMAIL_APP_PASSWORD:
        logger.warning("Email not configured — GMAIL_USER or GMAIL_APP_PASSWORD missing")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{_APP_NAME} <{_GMAIL_USER}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(_GMAIL_USER, _GMAIL_APP_PASSWORD)
            smtp.sendmail(_GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, token: str) -> bool:
    verify_url = f"{_APP_BASE_URL}?verify={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:2rem;">
      <h2 style="color:#2E7D32;">Welcome to {_APP_NAME}</h2>
      <p>Thanks for signing up. Please verify your email address by clicking the button below.</p>
      <p style="margin:1.5rem 0;">
        <a href="{verify_url}"
           style="background:#2E7D32;color:white;padding:0.7rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;">
          Verify Email Address
        </a>
      </p>
      <p style="color:#666;font-size:0.85rem;">
        This link expires in 24 hours. If you didn't create an account, you can ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#aaa;font-size:0.8rem;">
        Or copy this URL: {verify_url}
      </p>
    </div>
    """
    return _send(to_email, f"Verify your {_APP_NAME} account", html)


def send_password_reset_email(to_email: str, token: str) -> bool:
    reset_url = f"{_APP_BASE_URL}?reset={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:2rem;">
      <h2 style="color:#2E7D32;">{_APP_NAME} — Password Reset</h2>
      <p>We received a request to reset the password for your account.</p>
      <p style="margin:1.5rem 0;">
        <a href="{reset_url}"
           style="background:#2E7D32;color:white;padding:0.7rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;">
          Reset Password
        </a>
      </p>
      <p style="color:#666;font-size:0.85rem;">
        This link expires in 1 hour. If you didn't request a password reset, you can ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#aaa;font-size:0.8rem;">
        Or copy this URL: {reset_url}
      </p>
    </div>
    """
    return _send(to_email, f"Reset your {_APP_NAME} password", html)
