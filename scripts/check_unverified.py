"""Daily account-lifecycle job — entry point for Cloud Run Jobs.

Runs the two-phase pass:
  1. Send the final-warning email to anyone Pending for >24h with no reminder yet.
  2. Soft-delete (status='Removed') anyone whose reminder was sent >24h ago.

Then runs the SMTP canary: a login-only check against Gmail. If it fails, the
job logs SMTP_CANARY_FAILURE_TOKEN, which a Cloud Monitoring log-based alert
policy watches for and reports by email through Google's own alerting. That
detour matters — when the App Password dies, EVE's own mail is exactly what
cannot carry the news, so the alarm has to travel on a different channel. The
credential died twice (May and August 2026), the second time unnoticed for
three weeks, which is why this exists.

Designed for `python -m scripts.check_unverified` from the project root. Cloud
Scheduler triggers a Cloud Run Job built from the same Docker image as the web
app; the Job's entry-point command runs this script.

Exits with code 0 on success (even if individual users errored — those are
logged). Exits non-zero only if the top-level call raises.
"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger('check_unverified')


def run_smtp_canary() -> bool:
    """Log-only health check of the outgoing mail channel.

    Never raises and never changes the job's exit code: a broken mail
    credential must not make the lifecycle pass look failed, and a lifecycle
    failure must not mask the canary. The alerting is done by Cloud
    Monitoring matching the token in the log line below.
    """
    try:
        from utils.email_utils import check_smtp_login, SMTP_CANARY_FAILURE_TOKEN
        ok, detail = check_smtp_login()
    except Exception as e:
        from utils.email_utils import SMTP_CANARY_FAILURE_TOKEN
        ok, detail = False, f"canary itself failed: {e}"
    if ok:
        logger.info("SMTP canary OK — %s", detail)
        return True
    logger.error(
        "%s — EVE cannot send email. %s. Rotate the Gmail App Password at "
        "myaccount.google.com/apppasswords and update GMAIL_APP_PASSWORD on "
        "eve-valuation-engine, eve-valuation-engine-staging, "
        "eve-account-lifecycle and eve-account-lifecycle-staging.",
        SMTP_CANARY_FAILURE_TOKEN, detail,
    )
    return False


def main() -> int:
    from database import UserDB
    logger.info("Starting unverified-account lifecycle pass")
    counts = UserDB.process_unverified_accounts()
    logger.info(
        "Lifecycle pass done — reminded=%d, removed=%d, errors=%d",
        counts.get('reminded', 0),
        counts.get('removed', 0),
        counts.get('errors', 0),
    )
    run_smtp_canary()
    return 0


if __name__ == '__main__':
    sys.exit(main())
