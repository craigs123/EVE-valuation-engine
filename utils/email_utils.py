"""
Gmail SMTP helpers for account verification and password reset emails.
Requires env vars: GMAIL_USER, GMAIL_APP_PASSWORD
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

_GMAIL_USER = os.getenv('GMAIL_USER', '')
_GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')
_GMAIL_FROM = os.getenv('GMAIL_FROM', _GMAIL_USER)  # alias to send from (defaults to auth account)

_APP_NAME = "Ecosystem Valuation Engine"
_APP_BASE_URL = os.getenv('APP_BASE_URL', 'https://eve-valuation-engine-1025191764754.us-central1.run.app')
# Where new-signup notifications go. Comma-separated if more than one.
_ADMIN_NOTIFY_EMAILS = os.getenv('ADMIN_NOTIFY_EMAILS', 'craig@greenoxford.com')


def _send(to_email: str, subject: str, html_body: str) -> bool:
    if not _GMAIL_USER or not _GMAIL_APP_PASSWORD:
        logger.warning("Email not configured — GMAIL_USER or GMAIL_APP_PASSWORD missing")
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{_APP_NAME} <{_GMAIL_FROM}>"
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


# Distinctive token for the Cloud Monitoring log-based alert. Changing this
# string breaks the "EVE - email sending is broken" alert policy, whose filter
# matches on it. See scripts/check_unverified.py.
SMTP_CANARY_FAILURE_TOKEN = 'EVE_SMTP_CANARY_FAILED'


def check_smtp_login() -> tuple:
    """Authenticate against Gmail without sending anything.

    Returns (ok, detail). This is the whole of what breaks in practice: the
    App Password is revoked or expires, every send starts failing with
    535 BadCredentials, and because failures are logged and swallowed the
    only symptom is silence. Used by the nightly canary in the lifecycle job
    and by the admin panel's status line.
    """
    if not _GMAIL_USER or not _GMAIL_APP_PASSWORD:
        return False, "GMAIL_USER or GMAIL_APP_PASSWORD is not set"
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(_GMAIL_USER, _GMAIL_APP_PASSWORD)
        return True, f"Signed in to smtp.gmail.com as {_GMAIL_USER}"
    except smtplib.SMTPAuthenticationError as e:
        return False, (
            f"Gmail rejected the App Password for {_GMAIL_USER}: {e.smtp_code} "
            f"{e.smtp_error.decode(errors='replace') if isinstance(e.smtp_error, bytes) else e.smtp_error}"
        )
    except Exception as e:
        return False, f"Could not reach smtp.gmail.com as {_GMAIL_USER}: {e}"


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
        This link expires in 48 hours. If you didn't create an account, you can ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#aaa;font-size:0.8rem;">
        Or copy this URL: {verify_url}
      </p>
    </div>
    """
    return _send(to_email, f"Verify your {_APP_NAME} account", html)


def send_final_verification_warning_email(to_email: str, token: str) -> bool:
    """Final warning sent 24h after signup if the account is still unverified.
    Tells the user their access will be cut off if they don't verify within
    the next 24h."""
    verify_url = f"{_APP_BASE_URL}?verify={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:auto;padding:2rem;">
      <h2 style="color:#2E7D32;">{_APP_NAME} — Final reminder to verify</h2>
      <p>You signed up for {_APP_NAME} but haven't verified your email address yet.</p>
      <p style="background:#FFF4E5;border-left:4px solid #C62828;padding:0.85rem 1rem;
                margin:1.25rem 0;color:#1F2937;">
        <strong style="color:#B71C1C;">Important:</strong>
        <strong>Your account will be removed in 24 hours if you do not verify your email address.</strong>
        Click the button below to verify and keep your access.
      </p>
      <p style="margin:1.5rem 0;">
        <a href="{verify_url}"
           style="background:#2E7D32;color:white;padding:0.7rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;">
          Verify Email Address
        </a>
      </p>
      <p style="color:#666;font-size:0.85rem;">
        This link expires in 24 hours. If you no longer want an account, you can ignore this email
        and your details will be removed automatically.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#aaa;font-size:0.8rem;">
        Or copy this URL: {verify_url}
      </p>
    </div>
    """
    return _send(to_email, f"Final reminder — verify your {_APP_NAME} account", html)


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


def send_account_approved_email(to_email: str, display_name: Optional[str] = None) -> bool:
    """Sent when an admin approves a Pending account from inside the app,
    instead of the user clicking their verification link. The account is
    already usable by the time this goes out, so the email just tells them
    they can sign in."""
    greeting = f"Hi {display_name}," if display_name else "Hi,"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:auto;padding:2rem;">
      <h2 style="color:#2E7D32;">Your {_APP_NAME} account is ready</h2>
      <p>{greeting}</p>
      <p>An administrator has approved your account, so there's no need to
         click the verification link we sent you earlier. You can sign in now
         with the email address and password you registered with.</p>
      <p style="margin:1.5rem 0;">
        <a href="{_APP_BASE_URL}"
           style="background:#2E7D32;color:white;padding:0.7rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;">
          Sign in to {_APP_NAME}
        </a>
      </p>
      <p style="color:#666;font-size:0.85rem;">
        If you didn't create this account, please reply to this email and let us know.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#aaa;font-size:0.8rem;">
        Or copy this URL: {_APP_BASE_URL}
      </p>
    </div>
    """
    return _send(to_email, f"Your {_APP_NAME} account has been approved", html)


def _signup_digest_html(stats: Optional[dict]) -> str:
    """Account digest appended to the new-signup notification.

    Deliberately excludes any claim about email health — see the note in
    send_new_signup_notification(). removed_last_7_days is the line worth
    watching: a run of removals is what a broken mail channel looks like
    from the outside, since unverified accounts are cleared after 48h.
    """
    if not stats:
        return ''
    removed = stats.get('removed_last_7_days', 0)
    removed_style = 'color:#B71C1C;font-weight:600;' if removed else 'color:#1F2937;'
    return f"""
      <hr style="border:none;border-top:1px solid #eee;margin:1.5rem 0;">
      <p style="color:#666;font-size:0.85rem;margin-bottom:0.4rem;">Accounts right now</p>
      <table style="border-collapse:collapse;font-size:0.9rem;">
        <tr><td style="padding:0.2rem 1rem 0.2rem 0;color:#666;">Active</td>
            <td style="padding:0.2rem 0;">{stats.get('active', 0)}</td></tr>
        <tr><td style="padding:0.2rem 1rem 0.2rem 0;color:#666;">Awaiting approval</td>
            <td style="padding:0.2rem 0;">{stats.get('pending', 0)}</td></tr>
        <tr><td style="padding:0.2rem 1rem 0.2rem 0;color:#666;">Auto-removed, last 7 days</td>
            <td style="padding:0.2rem 0;{removed_style}">{removed}</td></tr>
      </table>
    """


def send_new_signup_notification(user_email: str, display_name: Optional[str] = None,
                                 organisation: Optional[str] = None,
                                 stats: Optional[dict] = None) -> bool:
    """Tell the administrators that someone has registered.

    Sent from UserDB.register() as soon as the account row exists, i.e. while
    it is still Pending and the user has not clicked their verification link.
    Recipients come from the ADMIN_NOTIFY_EMAILS env var (comma-separated),
    defaulting to the product owner. Failure is never allowed to affect the
    signup itself — the caller swallows exceptions.

    The app URL is included so a staging signup is distinguishable from a
    production one at a glance.

    `stats` is the optional account digest from UserDB.account_summary() —
    passed in rather than fetched here so this module keeps no database
    dependency. Note what this email can and cannot tell you: its arrival
    proves the mail channel works, so there is deliberately no "SMTP healthy"
    line. A dead App Password can never report itself this way; that is the
    nightly canary's job (scripts/check_unverified.py) and the Cloud
    Monitoring alert that watches for SMTP_CANARY_FAILURE_TOKEN.
    """
    recipients = [a.strip() for a in _ADMIN_NOTIFY_EMAILS.split(',') if a.strip()]
    if not recipients:
        return False
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:auto;padding:2rem;">
      <h2 style="color:#2E7D32;">New {_APP_NAME} signup</h2>
      <table style="border-collapse:collapse;font-size:0.95rem;">
        <tr><td style="padding:0.3rem 1rem 0.3rem 0;color:#666;">Email</td>
            <td style="padding:0.3rem 0;"><strong>{user_email}</strong></td></tr>
        <tr><td style="padding:0.3rem 1rem 0.3rem 0;color:#666;">Name</td>
            <td style="padding:0.3rem 0;">{display_name or '—'}</td></tr>
        <tr><td style="padding:0.3rem 1rem 0.3rem 0;color:#666;">Organisation</td>
            <td style="padding:0.3rem 0;">{organisation or '—'}</td></tr>
        <tr><td style="padding:0.3rem 1rem 0.3rem 0;color:#666;">App</td>
            <td style="padding:0.3rem 0;">{_APP_BASE_URL}</td></tr>
      </table>
      <p style="color:#666;font-size:0.9rem;margin-top:1.25rem;">
        The account is <strong>Pending</strong> until they click the verification
        link we have just emailed them. If they don't, it is removed automatically
        48 hours after signup — you can approve it by hand before then under
        <em>Analysis Settings → User Administration</em>.
      </p>
      <p style="margin:1.5rem 0;">
        <a href="{_APP_BASE_URL}"
           style="background:#2E7D32;color:white;padding:0.7rem 1.4rem;border-radius:6px;text-decoration:none;font-weight:600;">
          Open {_APP_NAME}
        </a>
      </p>
      {_signup_digest_html(stats)}
    </div>
    """
    sent = False
    for recipient in recipients:
        if _send(recipient, f"New {_APP_NAME} signup: {user_email}", html):
            sent = True
    return sent
