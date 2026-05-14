# Auth Persistence Plan (branch: `auth-persist-cookie`)

Working scope doc for persisting `auth_user` across Streamlit session resets. Delete this file when the implementation lands.

## Why

`utils/auth.py` stores the logged-in user only in `st.session_state['auth_user']`. Streamlit session state is in-memory, keyed by session ID, and resets on:

- WebSocket disconnect / reconnect (network blip, idle timeout, tab inactive)
- Cloud Run cold-start (staging scales to zero; first request after a quiet period gets a fresh container)
- Streamlit server reload

When that happens, `auth_user` is gone, `require_login()` at `app.py:1821` shows the login screen, and the user has been "logged out" mid-session. Symptom: occasional re-login prompts after periods of inactivity (e.g. picking a test area, leaving the tab, drawing a new area).

## Goal

Survive any Streamlit session reset without re-prompting the user. Login persists for ~30 days, refreshed on use. Sign-out actually signs out (clears both session state and the persisted credential).

## Approach

Signed-cookie + lazy hydration. Cookie holds the user ID + expiry, signed with `SESSION_SECRET` (already in env per `feedback_env_vars.md`). On every render, if `session_state['auth_user']` is missing, validate the cookie and repopulate `auth_user` from `UserDB`.

Why not server-side sessions table? Adds DB writes on every render, more moving parts. The cookie is self-contained and the only DB hit is a single `UserDB.get_by_id` on hydration (which is the existing read path anyway).

## Dependency

`extra-streamlit-components` (the `CookieManager` widget). Mature, MIT-licensed, no native deps. Add to `pyproject.toml`.

Alternative considered: `streamlit-cookies-manager`. Less maintained, similar API. Sticking with `extra-streamlit-components`.

## Files touched

- `utils/auth.py` — the bulk of the work.
- `pyproject.toml` — add `extra-streamlit-components`.
- `app.py` — one new line near the top: hydrate from cookie before `require_login()`.
- `database.py` — confirm there's a `UserDB.get_by_id(user_id)` lookup; add it if missing.

## Changes in detail

### 1. Cookie helpers in `utils/auth.py`

```python
import hashlib
import hmac
import json
import os
import time
import base64

_COOKIE_NAME = "eve_auth"
_COOKIE_TTL_SECONDS = 30 * 24 * 3600  # 30 days
_SESSION_SECRET = os.getenv("SESSION_SECRET", "")

def _sign(payload: bytes) -> str:
    sig = hmac.new(_SESSION_SECRET.encode(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")

def _mint_token(user_id: str) -> str:
    body = {"uid": user_id, "exp": int(time.time()) + _COOKIE_TTL_SECONDS}
    body_b = base64.urlsafe_b64encode(json.dumps(body).encode()).rstrip(b"=").decode()
    return f"{body_b}.{_sign(body_b.encode())}"

def _verify_token(token: str) -> str | None:
    """Return user_id if valid + unexpired, else None."""
    try:
        body_b, sig = token.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body_b.encode())):
            return None
        body = json.loads(base64.urlsafe_b64decode(body_b + "==="))
        if body.get("exp", 0) < int(time.time()):
            return None
        return body["uid"]
    except Exception:
        return None
```

HMAC-SHA256 with `SESSION_SECRET`. Constant-time compare via `hmac.compare_digest`. JSON body holds `uid` + `exp`. Base64url for URL safety.

### 2. CookieManager wrapper

```python
import extra_streamlit_components as stx

@st.cache_resource
def _cookie_manager() -> stx.CookieManager:
    return stx.CookieManager(key="eve_cookies")
```

Cached as a resource so the same manager instance is reused across reruns (it has a per-instance widget key).

### 3. Wire `hydrate_from_cookie()` + update `require_login` and `logout`

```python
def hydrate_from_cookie() -> None:
    """If session_state['auth_user'] is missing but a valid cookie exists,
    fetch the user from DB and repopulate session_state."""
    if st.session_state.get("auth_user"):
        return
    cm = _cookie_manager()
    token = cm.get(_COOKIE_NAME)
    if not token:
        return
    uid = _verify_token(token)
    if not uid:
        return
    from database import UserDB
    user = UserDB.get_by_id(uid)
    if user:
        st.session_state["auth_user"] = user

def require_login():
    hydrate_from_cookie()
    if st.session_state.get("auth_user"):
        return
    _render_auth_ui()
    st.stop()

def logout():
    cm = _cookie_manager()
    cm.delete(_COOKIE_NAME)
    for key in ("auth_user",):
        if key in st.session_state:
            del st.session_state[key]
```

### 4. Mint cookie on successful login

In `_render_auth_ui()`'s sign-in submit branch, after setting `st.session_state.auth_user = user`:

```python
cm = _cookie_manager()
cm.set(
    _COOKIE_NAME,
    _mint_token(user["id"]),
    expires_at=datetime.now() + timedelta(seconds=_COOKIE_TTL_SECONDS),
)
```

Same in the registration submit branch if it auto-signs-in (it doesn't today — sign-up requires email verification first, so this is only needed in the sign-in path).

### 5. `database.py` — confirm `UserDB.get_by_id`

Quickly verify there's an existing `UserDB.get_by_id(user_id)` returning the same dict shape as `UserDB.authenticate`. If not, add it — straight `SELECT * FROM users WHERE id = :id`. Should already exist for analyses/saved-areas lookups but worth confirming.

## Edge cases

- **`SESSION_SECRET` not set**: `_sign` produces a deterministic signature but anyone can forge. Mitigation: refuse to mint/verify tokens if `SESSION_SECRET` is empty (log a warning). Fall back to current session-only behavior. Prod and staging both have it set per memory.
- **Cookie present but user deleted from DB**: `get_by_id` returns None → don't populate session, render login screen. User reauthenticates.
- **Token expired**: `_verify_token` returns None → same behavior as no cookie.
- **Email not verified state**: the existing sign-in path already gates on `email_verified`. Hydration is symmetric — if the cookie was minted for a verified user, that's the state we restore. If a user's `email_verified` flag is revoked, they'd remain "signed in" until cookie expiry. Acceptable risk; an admin revoking verification can also delete the user.
- **Multiple tabs / multiple browsers**: each holds its own cookie. Sign-out in one tab clears only that browser's cookie; other browsers stay signed in until their tokens expire. Matches user expectations.
- **`extra-streamlit-components` async behavior**: CookieManager reads cookies via a JS roundtrip; the first render after page load may not have the cookie yet (`get` returns None). Acceptable — on the next rerun the cookie is available. Worst case: one flash of the login screen on the very first page load after the JS round-trip completes. If that's visible enough to matter, we can add a one-shot `st.spinner` while the manager initializes — but ship without it first and see.

## Verification

1. Sign in → confirm cookie `eve_auth` exists in browser DevTools → Application → Cookies.
2. Refresh the page → still signed in, no login screen flash longer than ~200ms.
3. Force a Streamlit session reset:
   - Sign in
   - In Cloud Run, scale the service down then back up (`gcloud run services update --min-instances=0 --max-instances=0` then back to defaults), OR
   - Open the app, wait for staging cold-start by leaving it idle 15+ minutes, then interact.
4. Confirm interaction succeeds without redirect to login screen.
5. Sign out → cookie is gone in DevTools, login screen appears.
6. Tamper test: edit the cookie value in DevTools to garbage → refresh → login screen (don't crash, don't auto-populate).
7. Multi-browser: sign in on Chrome, open Firefox → Firefox sees login screen (separate cookie jar). Sign in on Firefox → both signed in independently. Sign out on Chrome → Firefox still signed in.
8. Email-verification flow: register a new account → confirm sign-in still gates on `email_verified` and doesn't mint a cookie for an unverified user.

## Out of scope

- "Remember me" checkbox — always persist via cookie for now; revisit if users want a "do not remember" option.
- Server-side session revocation list — adds DB complexity for a feature we don't need yet (token expiry + secret rotation is sufficient).
- Cookie rotation on each request (sliding TTL refresh) — nice to have, but a 30-day fixed TTL is fine for the first cut.
- Migrating other session-state keys (analysis results, area selections) to survive reset — out of scope; users already accept that drawing in-progress work is lost on session reset. Auth is the only piece that breaks the UX badly.

## Sequence to land

1. PR `auth-persist-cookie` → `staging`. Bump to `v3.6.x-rcN` per the staging release-candidate convention in `CLAUDE.md` (or roll into the next `v3.6.x beta` if we keep the beta naming).
2. Deploy to staging, verify the matrix above.
3. PR `staging` → `main` once stable. Prod deploy bumps to `v3.6.x` clean.
4. Once prod is healthy for ~24 hours, delete this scope file.
