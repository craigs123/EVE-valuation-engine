"""
Authentication utilities for EVE — password hashing, session state helpers, login/register UI.
"""

import re
import streamlit as st


def hash_password(plain: str) -> str:
    import bcrypt
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))


def get_current_user():
    """Return the logged-in user dict {'id', 'email', 'display_name'}, or None."""
    return st.session_state.get('auth_user')


def logout():
    """Clear auth keys from session state."""
    for key in ('auth_user',):
        if key in st.session_state:
            del st.session_state[key]


def require_login():
    """Render login/register UI and call st.stop() if no authenticated user."""
    if st.session_state.get('auth_user'):
        return
    _render_auth_ui()
    st.stop()


# --- private helpers ---

_EMAIL_RE = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def _render_auth_ui():
    from database import UserDB

    st.markdown("""
    <div style="text-align:center; padding: 2.5rem 0 1.5rem 0;">
        <div style="font-size:3rem; line-height:1;">🌱</div>
        <h1 style="color:#2E7D32; font-size:1.9rem; font-weight:700; margin:0.6rem 0 0.3rem 0;">
            Ecosystem Valuation Engine
        </h1>
        <p style="color:#555; font-size:0.9rem; margin:0;">
            Sign in to access your workspace and run ecosystem analyses.
        </p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab_in, tab_reg = st.tabs(["Sign In", "Create Account"])

        # ---- Sign In ----
        with tab_in:
            email = st.text_input("Email", key="login_email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign in", type="primary", use_container_width=True, key="login_btn"):
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    user = UserDB.login(email.strip(), password)
                    if user:
                        st.session_state['auth_user'] = user
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")

        # ---- Create Account ----
        with tab_reg:
            reg_email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
            reg_name = st.text_input("Display name (optional)", key="reg_name",
                                     placeholder="Your name")
            reg_password = st.text_input("Password", type="password", key="reg_password",
                                         help="At least 8 characters")
            reg_confirm = st.text_input("Confirm password", type="password", key="reg_confirm")

            if st.button("Create account", type="primary", use_container_width=True, key="reg_btn"):
                errors = []
                if not reg_email or not _EMAIL_RE.match(reg_email.strip()):
                    errors.append("Please enter a valid email address.")
                if len(reg_password) < 8:
                    errors.append("Password must be at least 8 characters.")
                if reg_password != reg_confirm:
                    errors.append("Passwords do not match.")

                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    try:
                        user = UserDB.register(
                            reg_email.strip(),
                            reg_password,
                            reg_name.strip() or None,
                        )
                        st.session_state['auth_user'] = user
                        st.success("Account created — welcome to EVE!")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")
