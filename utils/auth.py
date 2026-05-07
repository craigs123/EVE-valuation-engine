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
    """Return the logged-in user dict {'id', 'email', 'display_name', 'email_verified'}, or None."""
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
    <style>
    .auth-tab-panel { padding-top: 1.4rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { padding: 0.5rem 1.2rem; }
    </style>
    <div style="text-align:center; padding: 3rem 0 2rem 0;">
        <div style="font-size:3rem; line-height:1;">🌱</div>
        <h1 style="color:#2E7D32; font-size:1.9rem; font-weight:700; margin:0.8rem 0 0.5rem 0;">
            Ecosystem Valuation Engine
        </h1>
        <p style="color:#555; font-size:0.95rem; margin:0 0 0.3rem 0;">
            Sign in to access your workspace and run ecosystem analyses.
        </p>
        <p style="color:#aaa; font-size:0.75rem; margin:0;">v3.5.1 beta</p>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
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
                    submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

                if submitted:
                    if not email or not password:
                        st.error("Please enter your email and password.")
                    else:
                        user = UserDB.login(email.strip(), password)
                        if user:
                            st.session_state['auth_user'] = user
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")

                st.markdown(
                    "<p style='text-align:right;margin-top:0.3rem;'>"
                    "<small><a href='#' id='forgot-pw-link' style='color:#2E7D32;'>Forgot password?</a></small>"
                    "</p>",
                    unsafe_allow_html=True,
                )
                if st.button("Forgot password?", key="forgot_pw_btn",
                             help="Reset your password via email",
                             use_container_width=False):
                    st.session_state['_show_forgot_pw'] = True
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Create Account ----
        with tab_reg:
            st.markdown("<div class='auth-tab-panel'>", unsafe_allow_html=True)
            reg_email = st.text_input("Email", key="reg_email", placeholder="you@example.com")
            reg_name = st.text_input("Display name (optional)", key="reg_name",
                                     placeholder="Your name")
            reg_password = st.text_input("Password", type="password", key="reg_password",
                                         help="At least 8 characters")
            reg_confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
            st.markdown("</div>", unsafe_allow_html=True)

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
                        st.session_state['_just_registered'] = True
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception as exc:
                        st.error(f"Registration failed: {exc}")
