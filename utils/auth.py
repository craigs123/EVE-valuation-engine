"""
Authentication utilities for EVE — password hashing, session state helpers, login/register UI.
"""

import base64
import hashlib
import hmac
import json
import os
import re
import time

import streamlit as st


def hash_password(plain: str) -> str:
    import bcrypt
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def get_current_user():
    """Return the logged-in user dict {'id', 'email', 'display_name', 'email_verified'}, or None."""
    return st.session_state.get('auth_user')


def logout():
    """Clear auth keys from session state and remove the persistence cookie."""
    _delete_auth_cookie()
    for key in ('auth_user',):
        if key in st.session_state:
            del st.session_state[key]
    # Cookie deletion via the CookieManager is asynchronous: the next render
    # still sees the stale cookie and hydrate_from_cookie() would log the user
    # straight back in. This flag suppresses hydration until an explicit sign-in
    # (a successful login wipes all session state, clearing the flag).
    st.session_state['_auth_signed_out'] = True


def require_login():
    """Render login/register UI and call st.stop() if no authenticated user.

    Tries cookie hydration first so users coming back from a Streamlit
    session reset (cold-start, websocket reconnect) stay signed in.
    """
    hydrate_from_cookie()
    if st.session_state.get('auth_user'):
        return
    _render_auth_ui()
    st.stop()


def hydrate_from_cookie() -> None:
    """If ``session_state['auth_user']`` is missing but a valid signed
    cookie exists, fetch the user from the DB and repopulate session
    state. Silent no-op when there's no cookie, the cookie is invalid,
    or persistence is disabled (missing SESSION_SECRET).
    """
    if st.session_state.get('auth_user'):
        return
    if st.session_state.get('_auth_signed_out'):
        # User signed out this session — ignore any not-yet-deleted cookie.
        return
    if not _session_secret():
        return
    token = _read_auth_cookie()
    if not token:
        return
    uid = _verify_token(token)
    if not uid:
        # Expired or tampered — drop it.
        _delete_auth_cookie()
        return
    try:
        from database import UserDB
        user = UserDB.get_by_id(uid)
    except Exception:
        user = None
    if user:
        st.session_state['auth_user'] = user
    else:
        # User no longer exists — clear the stale cookie.
        _delete_auth_cookie()


# --- private helpers ---

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


# --- cookie-based auth persistence ---
#
# Streamlit session state is in-memory and volatile (resets on websocket
# reconnect / Cloud Run cold-start / server reload). Without persistence
# the user is "logged out" every time the session resets. We mint a
# signed token at login, store it in a browser cookie, and re-hydrate
# session_state['auth_user'] on any render where it's missing.
#
# Token format: <base64url(json_body)>.<base64url(hmac_sha256(body))>
# json_body = {"uid": "<user_id>", "exp": <unix_seconds>}
#
# Step 1 of the plan adds only the crypto primitives (sign/mint/verify).
# CookieManager wiring + hydrate_from_cookie + login/logout integration
# arrive in subsequent steps. See AUTH_PERSISTENCE_PLAN.md.

_COOKIE_NAME = "eve_auth"
_COOKIE_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def _session_secret() -> str:
    """Read SESSION_SECRET at call time so test/dev env changes are picked up."""
    return os.getenv("SESSION_SECRET", "")


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(s: str) -> bytes:
    # Re-pad to a multiple of 4 before decoding.
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def _sign(payload: bytes) -> str:
    """HMAC-SHA256 sign payload with SESSION_SECRET. Returns urlsafe-b64 sig."""
    secret = _session_secret()
    if not secret:
        # No secret configured — refuse to sign. Callers (_mint_token,
        # _verify_token) treat this as "persistence disabled" and fall back
        # to session-only auth.
        return ""
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).digest()
    return _b64url_encode(sig)


def _mint_token(user_id: str) -> str | None:
    """Mint a signed cookie token for the given user_id. Returns None if
    SESSION_SECRET isn't configured."""
    if not _session_secret():
        return None
    body = {"uid": user_id, "exp": int(time.time()) + _COOKIE_TTL_SECONDS}
    body_b64 = _b64url_encode(json.dumps(body, separators=(",", ":")).encode("utf-8"))
    sig = _sign(body_b64.encode("utf-8"))
    if not sig:
        return None
    return f"{body_b64}.{sig}"


def _verify_token(token: str) -> str | None:
    """Return user_id if the token is well-formed, the signature is valid,
    and the expiry is in the future. Otherwise None. Never raises."""
    if not token or not _session_secret():
        return None
    try:
        body_b64, sig = token.split(".", 1)
    except ValueError:
        return None
    expected_sig = _sign(body_b64.encode("utf-8"))
    if not expected_sig or not hmac.compare_digest(sig, expected_sig):
        return None
    try:
        body = json.loads(_b64url_decode(body_b64).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    uid = body.get("uid")
    exp = body.get("exp", 0)
    if not isinstance(uid, str) or not isinstance(exp, (int, float)):
        return None
    if exp < time.time():
        return None
    return uid


# --- cookie I/O via extra-streamlit-components ---


def _cookie_manager():
    """Return a per-session CookieManager singleton stored in session_state.

    Why not ``@st.cache_resource``? CookieManager renders a Streamlit
    component during ``__init__``. Caching it via ``@st.cache_resource``
    trips ``CachedWidgetWarning`` on older Streamlit, and the escape-
    hatch flag (``experimental_allow_widgets``) was removed in newer
    Streamlit, breaking with ``TypeError``. Session-state caching sits
    outside Streamlit's cache machinery so neither problem applies.

    Why a singleton at all (vs. instantiating each call)? A single
    render can call _cookie_manager() more than once — e.g. the login
    submit render reads via hydrate_from_cookie then writes via
    _persist_auth_cookie. Re-constructing CookieManager would issue a
    duplicate widget-key call.
    """
    mgr = st.session_state.get('_eve_cookie_mgr')
    if mgr is None:
        import extra_streamlit_components as stx
        mgr = stx.CookieManager(key="eve_cookie_manager")
        st.session_state['_eve_cookie_mgr'] = mgr
    return mgr


def _read_auth_cookie() -> str | None:
    """Return the persisted auth-cookie value, or None if absent / not
    yet available (the underlying JS round-trip can take one render
    before cookies are visible to Python)."""
    try:
        cm = _cookie_manager()
        # Calling .get_all() at least once primes the manager; .get()
        # then returns the value if present.
        cm.get_all()
        return cm.get(_COOKIE_NAME)
    except Exception:
        return None


def _write_auth_cookie(token: str) -> None:
    """Set the auth cookie with the configured TTL. Silently no-ops if
    the cookie manager isn't available."""
    try:
        from datetime import datetime, timedelta, timezone
        cm = _cookie_manager()
        cm.set(
            _COOKIE_NAME,
            token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=_COOKIE_TTL_SECONDS),
            key=f"_cookie_set_{int(time.time())}",
        )
    except Exception:
        pass


def _delete_auth_cookie() -> None:
    """Remove the auth cookie. Silently no-ops if it doesn't exist or
    the cookie manager isn't available."""
    try:
        cm = _cookie_manager()
        if cm.get(_COOKIE_NAME) is not None:
            cm.delete(_COOKIE_NAME, key=f"_cookie_del_{int(time.time())}")
    except Exception:
        pass


def _persist_auth_cookie(user: dict) -> None:
    """Mint a signed token for ``user`` and store it in the auth cookie.
    No-op if persistence is disabled (missing SESSION_SECRET) or the
    user dict has no id."""
    uid = (user or {}).get("id")
    if not uid:
        return
    token = _mint_token(uid)
    if not token:
        return
    _write_auth_cookie(token)


def _render_auth_ui():
    from database import UserDB

    st.markdown("""
    <style>
    /* Forest-canopy background photo with a soft white-green scrim so form
       contents remain readable. Applied only on the login page (this UI is
       gated by require_login and exits via st.stop on the main app). */
    [data-testid="stAppViewContainer"] {
        /* Light scrim only — the hero and auth_card carry their own opaque
           backdrops, so the photo can show through everywhere else. */
        background:
            linear-gradient(rgba(255, 255, 255, 0.18), rgba(232, 245, 233, 0.12)),
            url('/app/static/login-bg.jpg') center center / cover no-repeat fixed;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    /* Pull the page content up — Streamlit's default block-container has
       ~6rem of top padding which pushes the hero too far down on 1080p. */
    [data-testid="stMain"] .block-container,
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    .auth-tab-panel { padding-top: 0.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.45rem 1.1rem; }
    .auth-hero {
        text-align: center;
        padding: 1.1rem 1.5rem 0.9rem 1.5rem;
        background: rgba(255, 255, 255, 0.75);
        border-radius: 16px;
        box-shadow: 0 8px 28px rgba(15, 23, 42, 0.10);
        max-width: 36rem;
        margin: 0.4rem auto 0.6rem auto;
        backdrop-filter: blur(6px);
        -webkit-backdrop-filter: blur(6px);
    }

    /* Tabs + form fields + footer attribution sit inside this keyed
       container so they get the same frosted-glass backdrop as the hero,
       keeping inputs and labels readable over the forest photo. */
    [class*="st-key-auth_card"] {
        background: rgba(255, 255, 255, 0.80) !important;
        border-radius: 16px !important;
        padding: 0.85rem 1.5rem 0.85rem 1.5rem !important;
        box-shadow: 0 8px 28px rgba(15, 23, 42, 0.10) !important;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    /* Drop the now-redundant separate background on the brand attribution
       div so it blends into the card */
    [class*="st-key-auth_card"] .auth-tab-panel {
        background: transparent !important;
    }
    /* Tighter spacing between form widgets inside the card */
    [class*="st-key-auth_card"] [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    [class*="st-key-auth_card"] .stTextInput {
        margin-bottom: 0 !important;
    }
    .auth-hero .mark { font-size:2.1rem; line-height:1; margin-bottom: 0.15rem; }
    .auth-hero h1 {
        color:#1F2937 !important; font-size:1.55rem !important;
        font-weight:700 !important; letter-spacing:-0.01em !important;
        margin:0.15rem auto 0.3rem auto !important;
    }
    .auth-hero .tagline,
    .auth-hero .sub {
        max-width:32rem !important;
        margin-left:auto !important;
        margin-right:auto !important;
        text-align:center !important;
    }
    .auth-hero .tagline {
        color:#374151 !important; font-size:0.95rem !important;
        font-weight:500 !important;
        margin-top:0 !important; margin-bottom:0.2rem !important;
    }
    .auth-hero .sub {
        color:#6B7280 !important; font-size:0.85rem !important;
        margin-top:0 !important; margin-bottom:0 !important;
    }
    .auth-hero .accent {
        width:42px; height:2px; background:#2E7D32;
        margin:0.7rem auto 0; border-radius:2px;
    }
    .auth-hero .ver {
        color:#9CA3AF !important; font-size:0.7rem !important;
        margin:0.55rem auto 0 auto !important;
        text-align:center !important;
    }
    </style>
    <div class="auth-hero">
        <div class="mark">🌱</div>
        <h1>Ecosystem Valuation Engine</h1>
        <p class="tagline">Empowering nature-based projects everywhere.</p>
        <p class="sub">Sign in to access your workspace and run ecosystem analyses.</p>
        <div class="accent"></div>
        <p class="ver">v3.8.4 beta &nbsp;·&nbsp; © 2026 Green &amp; Grey Associates</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
      with st.container(key="auth_card"):
        tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])

        # ---- Sign In ----
        with tab_in:
            st.markdown("<div class='auth-tab-panel'>", unsafe_allow_html=True)

            # Forgot-password flow lives inside an expander to avoid layout jumps
            if st.session_state.get('_show_forgot_pw'):
                st.markdown("**Reset your password**")
                fp_email = st.text_input("Enter your account email", key="fp_email",
                                         placeholder="you@example.com")
                col_send, col_back = st.columns(2)
                with col_send:
                    if st.button("Send reset link", type="primary", use_container_width=True, key="fp_send"):
                        if fp_email and _EMAIL_RE.match(fp_email.strip()):
                            UserDB.create_password_reset(fp_email.strip())
                            # Always show success to avoid email enumeration
                            st.success("If that email is registered you'll receive a reset link shortly.")
                            st.session_state['_show_forgot_pw'] = False
                        else:
                            st.error("Please enter a valid email address.")
                with col_back:
                    if st.button("← Back to sign in", use_container_width=True, key="fp_back"):
                        st.session_state['_show_forgot_pw'] = False
                        st.rerun()
            else:
                with st.form("login_form"):
                    email = st.text_input("Email", key="login_email", placeholder="you@example.com")
                    password = st.text_input("Password", type="password", key="login_password")
                    remember = st.checkbox(
                        "Remember me on this device", value=False, key="login_remember",
                        help="Stay signed in for 30 days on this browser. Leave "
                             "unchecked on shared or public computers — otherwise "
                             "you'll need to sign in again each visit.",
                    )
                    st.markdown("<div style='height:0.75rem;'></div>", unsafe_allow_html=True)
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter your email and password.")
                    else:
                        user, err = UserDB.login(email.strip(), password)
                        if user:
                            # Wipe any stale session state (map selection,
                            # analysis results, settings overrides, indicator
                            # responses, etc.) so the user starts fresh on
                            # every sign-in. The post-rerun render of the
                            # main app re-initialises its defaults.
                            for _k in list(st.session_state.keys()):
                                del st.session_state[_k]
                            st.session_state['auth_user'] = user
                            # Persist a signed cookie ONLY when the user opted
                            # in via "Remember me". Without it, a browser
                            # refresh / new session requires signing in again
                            # (this also means an involuntary Streamlit
                            # reconnect ends the session — the opt-in trade-off).
                            if remember:
                                _persist_auth_cookie(user)
                            st.rerun()
                        elif err == 'pending_verification':
                            st.error(
                                "Email has not been verified. Please check your "
                                "inbox and verify your email before returning here "
                                "and signing in."
                            )
                        elif err == 'removed':
                            st.error(
                                "This account has been removed because the email "
                                "was not verified in time. Use the **Create Account** "
                                "tab to sign up again with this email."
                            )
                        else:
                            st.error("Invalid email or password.")

                if st.button("Forgot password?", key="forgot_pw_btn",
                             help="Reset your password via email",
                             use_container_width=False):
                    st.session_state['_show_forgot_pw'] = True
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Create Account ----
        with tab_reg:
            st.markdown("<div class='auth-tab-panel'>", unsafe_allow_html=True)
            reg_email = st.text_input("Email *", key="reg_email", placeholder="you@example.com")
            reg_name = st.text_input("Display name *", key="reg_name",
                                     placeholder="Your name")
            reg_org = st.text_input("Organisation *", key="reg_org",
                                    placeholder="Your organisation or company")
            reg_password = st.text_input("Password *", type="password", key="reg_password",
                                         help="At least 8 characters")
            reg_confirm = st.text_input("Confirm password *", type="password", key="reg_confirm")
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("Create account", type="primary", use_container_width=True, key="reg_btn"):
                errors = []
                if not reg_email or not _EMAIL_RE.match(reg_email.strip()):
                    errors.append("Please enter a valid email address.")
                if not reg_name or not reg_name.strip():
                    errors.append("Please enter a display name.")
                if not reg_org or not reg_org.strip():
                    errors.append("Please enter your organisation.")
                if len(reg_password) < 8:
                    errors.append("Password must be at least 8 characters.")
                if reg_password != reg_confirm:
                    errors.append("Passwords do not match.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        UserDB.register(
                            reg_email.strip(),
                            reg_password,
                            reg_name.strip(),
                            reg_org.strip(),
                        )
                        # Do NOT log the user in — verification is required first.
                        st.success(
                            "Account created. A verification email has been sent — "
                            "please check your inbox (and your spam folder) and click "
                            "the verification link before signing in."
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")

            # Helper note for the form — placed below the button, right-justified,
            # so it doesn't add height to the form itself.
            st.markdown(
                "<div style='text-align:right; color:#6B7280; "
                "font-size:0.78rem; margin-top:0;'>"
                "* All fields are required."
                "</div>",
                unsafe_allow_html=True,
            )

        # Brand attribution sits inside the column so it stays narrow and
        # centred just below whichever tab's submit button is currently shown
        # (Forgot password on Sign In, Create account on Create Account).
        # Negative top margin pulls the logo block up to halve the visible gap
        # between the button and the logo (Streamlit inserts default spacing
        # between consecutive st.markdown blocks).
        st.markdown(
            """<div style='text-align:center; padding:0; margin-top:-0.75rem;'>
                <a href='https://www.greenandgreyassociates.com' target='_blank'
                   style='display:inline-block; margin-bottom:0.2rem;'>
                    <img src='/app/static/greengrey-logo.png'
                         alt='Green & Grey Associates'
                         style='height:80px; width:auto; opacity:0.85;' />
                </a>
                <div style='color:#6B7280; font-size:0.78rem;'>
                    Built by
                    <a href='https://www.greenandgreyassociates.com' target='_blank'
                       style='color:#2E7D32; text-decoration:none; font-weight:500;'>
                    Green &amp; Grey Associates</a>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
