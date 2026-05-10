"""Daily account-lifecycle job — entry point for Cloud Run Jobs.

Runs the two-phase pass:
  1. Send the final-warning email to anyone Pending for >24h with no reminder yet.
  2. Soft-delete (status='Removed') anyone whose reminder was sent >24h ago.

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
    return 0


if __name__ == '__main__':
    sys.exit(main())
