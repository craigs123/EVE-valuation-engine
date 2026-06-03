"""
Signup / email-verification flow tests.

Exercises the real ``UserDB`` account state machine (register → verify →
login, resend, expiry, re-registration of soft-deleted rows) plus the pure
token/email-URL helpers. No external services are touched:

  * The DB is an in-memory SQLite database with only the ``users`` table
    created from the real ``User`` model.
  * Email sending is monkeypatched so we capture the verification token
    instead of hitting Gmail SMTP.

Runnable without pytest:  ``python tests/test_signup_verification.py``
(Also discoverable by pytest if it is installed.)
"""

import os
import sys
from datetime import datetime, timedelta

# database.py builds its engine at import time and requires DATABASE_URL.
# A dummy postgres URL is enough — create_engine() does not connect until
# a session is actually used, and we rebind SessionLocal to SQLite below.
os.environ.setdefault("DATABASE_URL", "postgresql://u:p@localhost:5432/dummy")
os.environ.setdefault("SESSION_SECRET", "test-secret-for-token-signing")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

import database
from database import User, UserDB
from utils import email_utils


# ── test harness ──────────────────────────────────────────────────────────

_sent_emails: list[dict] = []


def _fresh_db():
    """Point database.SessionLocal at a clean in-memory SQLite DB holding
    just the users table, and return the engine (kept alive by the caller)."""
    eng = sa.create_engine("sqlite://")
    User.__table__.create(eng)
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=eng)
    return eng


def _install_email_capture(verification_ok=True):
    """Replace the email senders so registration/resend record the token
    instead of sending. Returns nothing; tokens land in _sent_emails."""
    def _cap(kind, ok):
        def _fn(to_email, token):
            _sent_emails.append({"kind": kind, "to": to_email, "token": token})
            return ok
        return _fn

    # UserDB imports these names *inside* the methods (from utils.email_utils
    # import ...), so patching the module attributes is sufficient.
    email_utils.send_verification_email = _cap("verify", verification_ok)
    email_utils.send_final_verification_warning_email = _cap("warning", verification_ok)
    email_utils.send_password_reset_email = _cap("reset", verification_ok)


# Minimal assert-based runner so this works with or without pytest.
_results = []


def _run(name, fn):
    global _sent_emails
    _sent_emails = []
    _fresh_db()
    _install_email_capture()
    try:
        fn()
        _results.append((name, True, None))
        print(f"  PASS  {name}")
    except AssertionError as e:
        _results.append((name, False, str(e) or "assertion failed"))
        print(f"  FAIL  {name}: {e}")
    except Exception as e:
        import traceback
        _results.append((name, False, repr(e)))
        print(f"  ERROR {name}: {e}")
        traceback.print_exc()


# ── DB state-machine tests ──────────────────────────────────────────────────

def test_happy_path_register_verify_login():
    reg = UserDB.register("alice@example.com", "password123", "Alice", "Acme")
    assert reg["status"] == "Pending", reg["status"]
    assert reg["email_verified"] is False
    assert reg["verification_email_sent"] is True, "register should report email sent"
    assert len(_sent_emails) == 1 and _sent_emails[0]["kind"] == "verify"

    # Cannot log in before verifying.
    user, err = UserDB.login("alice@example.com", "password123")
    assert user is None and err == "pending_verification", (user, err)

    # Verify with the emailed token.
    token = _sent_emails[0]["token"]
    assert UserDB.verify_email(token) is True

    # Now login succeeds and account is Active.
    user, err = UserDB.login("alice@example.com", "password123")
    assert err is None and user is not None, (user, err)
    assert user["status"] == "Active" and user["email_verified"] is True


def test_email_is_lowercased_and_login_case_insensitive():
    UserDB.register("Bob@Example.com", "password123", "Bob", "Acme")
    token = _sent_emails[0]["token"]
    UserDB.verify_email(token)
    # login with a differently-cased email must still work
    user, err = UserDB.login("BOB@example.COM", "password123")
    assert err is None and user is not None, (user, err)


def test_register_and_resend_token_ttl_is_48h():
    # The verification token must stay valid for ~48h so the original link
    # survives until the account's auto-removal point.
    UserDB.register("noah@example.com", "password123", "Noah", "Acme")
    with database.get_db() as db:
        u = db.query(User).filter(User.email == "noah@example.com").first()
        delta = u.verification_token_expiry - datetime.utcnow()
        assert timedelta(hours=47) < delta <= timedelta(hours=48), delta
    # Resend issues a fresh token with the same 48h window.
    UserDB.resend_verification("noah@example.com")
    with database.get_db() as db:
        u = db.query(User).filter(User.email == "noah@example.com").first()
        delta = u.verification_token_expiry - datetime.utcnow()
        assert timedelta(hours=47) < delta <= timedelta(hours=48), delta


def test_verify_email_is_idempotent_on_repeat_click():
    # Regression: a verification link is routinely opened more than once
    # (second device, page refresh, corporate link scanner / in-app browser).
    # The first open verifies; subsequent opens of the SAME link must still
    # report success rather than "expired or invalid".
    UserDB.register("liam@example.com", "password123", "Liam", "Acme")
    token = _sent_emails[0]["token"]
    assert UserDB.verify_email(token) is True, "first click verifies"
    assert UserDB.verify_email(token) is True, "second click stays idempotent"
    assert UserDB.verify_email(token) is True, "third click stays idempotent"
    # Login works throughout.
    user, err = UserDB.login("liam@example.com", "password123")
    assert err is None and user is not None and user["status"] == "Active"


def test_verify_email_idempotent_even_after_expiry():
    # Once Active, re-opening the link succeeds even if the token's original
    # 24h expiry has since passed (the account is genuinely verified).
    UserDB.register("mia@example.com", "password123", "Mia", "Acme")
    token = _sent_emails[0]["token"]
    assert UserDB.verify_email(token) is True
    with database.get_db() as db:
        u = db.query(User).filter(User.email == "mia@example.com").first()
        u.verification_token_expiry = datetime.utcnow() - timedelta(hours=1)
        db.commit()
    assert UserDB.verify_email(token) is True, "verified account re-click ignores expiry"


def test_verify_email_invalid_token():
    UserDB.register("carol@example.com", "password123", "Carol", "Acme")
    assert UserDB.verify_email("not-a-real-token") is False


def test_verify_email_expired_token():
    UserDB.register("dave@example.com", "password123", "Dave", "Acme")
    token = _sent_emails[0]["token"]
    # Force the token expiry into the past.
    with database.get_db() as db:
        u = db.query(User).filter(User.verification_token == token).first()
        u.verification_token_expiry = datetime.utcnow() - timedelta(minutes=1)
        db.commit()
    assert UserDB.verify_email(token) is False, "expired token must not verify"
    # Account stays Pending.
    user, err = UserDB.login("dave@example.com", "password123")
    assert err == "pending_verification", (user, err)


def test_duplicate_registration_rejected():
    UserDB.register("erin@example.com", "password123", "Erin", "Acme")
    try:
        UserDB.register("erin@example.com", "different", "Erin2", "Acme")
        assert False, "expected ValueError for duplicate email"
    except ValueError:
        pass


def test_reregister_over_removed_account_reactivates():
    UserDB.register("frank@example.com", "password123", "Frank", "Acme")
    # Soft-delete the account the way the lifecycle job would.
    with database.get_db() as db:
        u = db.query(User).filter(User.email == "frank@example.com").first()
        u.status = "Removed"
        u.password_hash = ""
        u.verification_token = None
        db.commit()
    # Re-registering must succeed and return to Pending with a fresh token.
    reg = UserDB.register("frank@example.com", "newpassword", "Frank", "Acme")
    assert reg["status"] == "Pending", reg["status"]
    token = _sent_emails[-1]["token"]
    assert token, "a fresh verification token should be issued"
    assert UserDB.verify_email(token) is True
    user, err = UserDB.login("frank@example.com", "newpassword")
    assert err is None and user is not None, (user, err)


def test_login_wrong_password():
    UserDB.register("gina@example.com", "password123", "Gina", "Acme")
    UserDB.verify_email(_sent_emails[0]["token"])
    user, err = UserDB.login("gina@example.com", "wrongpass")
    assert user is None and err == "invalid_credentials", (user, err)


def test_login_unknown_email():
    user, err = UserDB.login("nobody@example.com", "password123")
    assert user is None and err == "invalid_credentials", (user, err)


def test_login_removed_account():
    UserDB.register("hank@example.com", "password123", "Hank", "Acme")
    with database.get_db() as db:
        u = db.query(User).filter(User.email == "hank@example.com").first()
        u.status = "Removed"
        db.commit()
    user, err = UserDB.login("hank@example.com", "password123")
    assert user is None and err == "removed", (user, err)


def test_resend_verification_states():
    # Pending account → resend works and issues a new token.
    UserDB.register("ivy@example.com", "password123", "Ivy", "Acme")
    first_token = _sent_emails[0]["token"]
    assert UserDB.resend_verification("ivy@example.com") is True
    new_token = _sent_emails[-1]["token"]
    assert new_token != first_token, "resend should mint a fresh token"
    # The old token must no longer verify; the new one must.
    assert UserDB.verify_email(first_token) is False
    assert UserDB.verify_email(new_token) is True
    # Now Active → resend refuses.
    assert UserDB.resend_verification("ivy@example.com") is False
    # Unknown email → refuses.
    assert UserDB.resend_verification("ghost@example.com") is False


def test_register_reports_email_send_failure():
    # Simulate Gmail rejecting the send (the known prod failure mode).
    _install_email_capture(verification_ok=False)
    reg = UserDB.register("jack@example.com", "password123", "Jack", "Acme")
    assert reg["verification_email_sent"] is False, (
        "register must surface SMTP failure so the UI shows the resend hint"
    )
    # The account is still created and a token persisted, so a later resend
    # (once SMTP is fixed) can verify it.
    token = _sent_emails[0]["token"]
    assert UserDB.verify_email(token) is True


# ── pure helper tests (no DB) ───────────────────────────────────────────────

def test_token_mint_verify_roundtrip():
    from utils import auth
    uid = "11111111-1111-1111-1111-111111111111"
    tok = auth._mint_token(uid)
    assert tok and auth._verify_token(tok) == uid


def test_token_tamper_rejected():
    from utils import auth
    tok = auth._mint_token("22222222-2222-2222-2222-222222222222")
    body, sig = tok.split(".", 1)
    forged = body + "." + ("A" * len(sig))
    assert auth._verify_token(forged) is None


def test_token_requires_secret():
    from utils import auth
    old = os.environ.pop("SESSION_SECRET", None)
    try:
        assert auth._mint_token("x") is None
        assert auth._verify_token("anything.anything") is None
    finally:
        if old is not None:
            os.environ["SESSION_SECRET"] = old


def test_verification_email_url_contains_token():
    # Use the real builder but capture the outgoing _send call.
    import importlib
    eu = importlib.reload(email_utils)
    captured = {}

    def _fake_send(to, subject, html):
        captured["to"] = to
        captured["subject"] = subject
        captured["html"] = html
        return True

    eu._send = _fake_send
    eu.send_verification_email("kate@example.com", "TOKEN123")
    assert "?verify=TOKEN123" in captured["html"], captured.get("html", "")[:200]
    assert "kate@example.com" == captured["to"]
    # restore the patched module for any later tests
    _install_email_capture()


def test_send_returns_false_when_unconfigured():
    # The actual SMTP guard: no GMAIL creds → _send returns False (does not raise).
    import importlib
    for k in ("GMAIL_USER", "GMAIL_APP_PASSWORD"):
        os.environ.pop(k, None)
    eu = importlib.reload(email_utils)
    assert eu._send("x@example.com", "subj", "<p>body</p>") is False
    _install_email_capture()


# ── runner ──────────────────────────────────────────────────────────────────

_TESTS = [
    ("happy path register->verify->login", test_happy_path_register_verify_login),
    ("email lowercased / login case-insensitive", test_email_is_lowercased_and_login_case_insensitive),
    ("register/resend token TTL is 48h", test_register_and_resend_token_ttl_is_48h),
    ("verify_email idempotent on repeat click", test_verify_email_is_idempotent_on_repeat_click),
    ("verify_email idempotent even after expiry", test_verify_email_idempotent_even_after_expiry),
    ("verify_email rejects invalid token", test_verify_email_invalid_token),
    ("verify_email rejects expired token", test_verify_email_expired_token),
    ("duplicate registration rejected", test_duplicate_registration_rejected),
    ("re-register over Removed reactivates", test_reregister_over_removed_account_reactivates),
    ("login wrong password", test_login_wrong_password),
    ("login unknown email", test_login_unknown_email),
    ("login removed account", test_login_removed_account),
    ("resend verification states", test_resend_verification_states),
    ("register reports email send failure", test_register_reports_email_send_failure),
    ("token mint/verify roundtrip", test_token_mint_verify_roundtrip),
    ("token tamper rejected", test_token_tamper_rejected),
    ("token requires SESSION_SECRET", test_token_requires_secret),
    ("verification email URL contains token", test_verification_email_url_contains_token),
    ("_send returns False when unconfigured", test_send_returns_false_when_unconfigured),
]


def main():
    print("Running signup / verification flow tests\n")
    for name, fn in _TESTS:
        _run(name, fn)
    passed = sum(1 for _, ok, _ in _results if ok)
    failed = len(_results) - passed
    print(f"\n{passed} passed, {failed} failed, {len(_results)} total")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
