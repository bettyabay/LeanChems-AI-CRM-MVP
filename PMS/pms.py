import streamlit as st
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import uuid
import google.generativeai as genai
import PyPDF2
import io
from docx import Document
import base64
from datetime import datetime
from typing import Any, Dict
try:
    from groq import Groq  # type: ignore
except Exception:  # groq sdk may not be installed in some environments
    Groq = None  # type: ignore

# Page config
def main():
    st.set_page_config(
        page_title="Leanchems Product Management System",
        page_icon="🧪",
        layout="wide",  # Changed from "centered" to "wide"
        initial_sidebar_state="collapsed"
    )

# --- Enhanced Custom CSS for Modern UI ---
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global Styles */
.stApp {
    background: #f3f9ff; /* Very light blue after login */
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Login screen background - only when not authenticated */
.stApp:has(.wide-login-container) {
    background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 100%);
}

/* Main content container */
.main .block-container {
    background: rgba(248, 250, 252, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1rem 2rem;
    margin: 0.25rem;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(147, 197, 253, 0.15);
    max-width: 4000px;
    width: 98vw;
    margin-left: auto;
    margin-right: auto;
    min-height: calc(100vh - 200px);
    height: auto;
}

/* Dashboard content spacing and layout */
.dashboard-content {
    padding: 0.5rem 0;
    min-height: calc(100vh - 300px);
    width: 100%;
}

/* Feature boxes and form cards spacing */
.feature-box, .form-card {
    margin: 1rem 0;
    padding: 1.5rem;
    width: 100%;
}

/* Remove default Streamlit padding that creates gaps */
.stMarkdown, .stDataFrame, .stButton, .stSelectbox, .stTextInput, .stTextArea {
    margin: 0;
    padding: 0;
}

/* Additional layout improvements */
.stApp > div:first-child {
    padding: 0;
    margin: 0;
}

/* Ensure content flows properly */
.main .block-container > div {
    margin: 0;
    padding: 0;
}

/* Better spacing for form elements */
.stForm > div {
    margin: 0.5rem 0;
    padding: 0;
}

/* Login Screen Styling */
            .login-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 0.5rem 0.25rem;
                margin: 1rem auto;
                max-width: 100px;
                width: 100px;
                box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }

/* Header Enhancements */
.header-container {
    background: rgba(248, 250, 252, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 1.5rem 2rem;
    margin: 0.25rem 0.25rem 1rem 0.25rem;
    border: 1px solid rgba(147, 197, 253, 0.15);
    max-width: 4000px;
    width: 98vw;
    margin-left: auto;
    margin-right: auto;
}

/* Navigation Button Styling */
.nav-button {
    background: linear-gradient(145deg, #f8fafc, #e2e8f0);
    border: 1px solid rgba(147, 197, 253, 0.3);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin: 0.5rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
}

.nav-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(147, 197, 253, 0.15);
    border-color: #93c5fd;
    background: linear-gradient(145deg, #93c5fd, #60a5fa);
    color: white;
}

.nav-button.active {
    background: linear-gradient(145deg, #93c5fd, #60a5fa);
    color: white;
    border-color: #93c5fd;
    box-shadow: 0 8px 25px rgba(147, 197, 253, 0.25);
}

/* Input Field Styling */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(147, 197, 253, 0.2);
                border-radius: 12px;
                padding: 0.75rem 1rem;
                font-size: 0.95rem;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                /* Removed global width constraints */
            }
            
            /* Responsive login form inputs */
            .login-container [data-testid="stTextInput"],
            .login-container [data-testid="stTextInput"] > div,
            .login-container [data-testid="stTextInput"] > div > div,
            .login-container [data-testid="stTextInput"] > div > div > input,
            .login-container form,
            .login-container form > div {
                max-width: 100% !important;
                width: 100% !important;
                min-width: 0 !important;
            }

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stSelectbox > div > div > select:focus {
    border-color: #93c5fd;
    box-shadow: 0 0 0 3px rgba(147, 197, 253, 0.1);
    outline: none;
}

/* Button Styling */
button[kind="primary"] {
    background: linear-gradient(145deg, #93c5fd, #60a5fa);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.75rem 2rem;
    font-weight: 600;
    font-size: 0.95rem;
    box-shadow: 0 6px 20px rgba(147, 197, 253, 0.3);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
}

button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(147, 197, 253, 0.4);
}

button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.9);
    color: #93c5fd;
    border: 2px solid rgba(147, 197, 253, 0.3);
    border-radius: 12px;
    padding: 0.75rem 1.5rem;
    font-weight: 500;
    transition: all 0.3s ease;
}

/* Equal-size ONLY for the top nav module buttons */
.nav-buttons button[kind="primary"],
.nav-buttons button[kind="secondary"] {
    height: 120px;
    min-height: 120px;
    width: 100%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    white-space: normal;
    text-align: center;
    line-height: 1.2;
    word-break: break-word;
    color: #111 !important; /* improve readability of nav labels */
    text-shadow: none !important;
}

button[kind="secondary"]:hover {
    background: rgba(147, 197, 253, 0.1);
    border-color: #93c5fd;
    transform: translateY(-1px);
}

/* Header Typography */
h1, h2, h3, h4 {
    color: #2d3748;
    font-weight: 700;
    margin-bottom: 1.5rem;
    letter-spacing: -0.025em;
}

h1 {
    background: linear-gradient(145deg, #93c5fd, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem;
}

h2 {
    color: #4a5568;
    font-size: 1.875rem;
}

/* Card Styling */
.feature-box, .form-card {
    background: rgba(248, 250, 252, 0.95);
    backdrop-filter: blur(15px);
    padding: 1.5rem;
    border-radius: 16px;
    margin: 0.75rem 0;
    border: 1px solid rgba(147, 197, 253, 0.15);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
}

/* Hide empty form-card elements */
.form-card:empty {
    display: none;
}

.feature-box:hover, .form-card:hover {
    transform: translateY(-4px);
}

/* Expander Styling */
.streamlit-expanderHeader {
    background: linear-gradient(145deg, #f7fafc, #edf2f7);
    border-radius: 12px;
    border: 1px solid rgba(147, 197, 253, 0.2);
    font-weight: 600;
    color: #4a5568;
}

/* Sidebar Enhancements */
.css-1d391kg, .css-1v0mbdj {
    background: rgba(248, 250, 252, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(147, 197, 253, 0.15);
}

/* Success/Error Messages */
.stSuccess {
    background: linear-gradient(145deg, #48bb78, #38a169);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    border: none;
}

.stError {
    background: linear-gradient(145deg, #f56565, #e53e3e);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    border: none;
}

.stWarning {
    background: linear-gradient(145deg, #ed8936, #dd6b20);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    border: none;
}

.stInfo {
    background: linear-gradient(145deg, #4299e1, #3182ce);
    color: white;
    border-radius: 12px;
    padding: 1rem;
    border: none;
}

/* Hide Streamlit Default Elements */
.stTextInput > div > div > input + div,
.stDeployButton,
.stDecoration {
    display: none;
}

/* Caption Styling */
.caption {
    color: #718096;
    font-size: 0.875rem;
    font-weight: 500;
}

/* Metrics and Statistics */
.metric-card {
    background: linear-gradient(145deg, #ffffff, #f7fafc);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(147, 197, 253, 0.1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

/* Animation Classes */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fadeInUp 0.6s ease-out;
}

/* Responsive Design */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem;
        margin: 0.5rem;
    }
    
    .login-container {
        margin: 1rem;
        padding: 2rem 1.5rem;
    }
    
    h1 {
        font-size: 2rem;
    }
}

.hint { 
    color: #718096; 
    font-size: 0.875rem;
    font-weight: 400;
}

/* Dark mode adjustments */
@media (prefers-color-scheme: dark) {
    :root, .stApp {
        --bg: #0E1117;
        --panel: #262730;
        --text: #FAFAFA;
        --muted: #CBD5E1;
    }
    body { background-color: var(--bg); }
    .stApp { background-color: var(--bg); }
    .stApp:has(.wide-login-container) {
        background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 100%);
    }
    .main .block-container { background: rgba(22, 27, 34, 0.85); }
    .css-1d391kg, .css-1v0mbdj, .feature-box, .form-card {
        background-color: var(--panel);
        color: var(--text);
    }
    /* Ensure all text is readable */
    .stApp, .stApp * { color: #FAFAFA !important; }

    /* Fix inline hard-coded colors */
    h1, h2, h3, h4, p, span, div { color: #FAFAFA !important; }

    /* Muted text (secondary info) */
    .hint, .caption, small { color: #A0AEC0 !important; }

    /* Input fields */
    input, textarea, select {
        border: 1px solid #444;
        background-color: #1F2430 !important;
        color: #FAFAFA !important;
    }
    ::placeholder { color: #9CA3AF !important; }

    /* Buttons */
    button[kind="primary"], button[kind="secondary"] { color: #ffffff !important; }
    a { color: #93c5fd !important; }
    .stAlert, [role="alert"] { color: #ffffff !important; }
}

.wide-login-container {
    background: linear-gradient(135deg, #f8fafc, #e2e8f0);
    backdrop-filter: blur(20px);
    border-radius: 25px;
    padding: 2rem 3rem;
    margin: 1.5rem auto;
    max-width: 4000px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

</style>
<style>
/* Smaller buttons in Manage Partners */
.partner-actions button[kind="primary"],
.partner-actions button[kind="secondary"],
.partner-actions button {
    padding: 0.4rem 0.8rem !important;
    font-size: 0.85rem !important;
    border-radius: 8px !important;
}
.partner-actions-small button {
    padding: 0.35rem 0.7rem !important;
    font-size: 0.8rem !important;
}
.partner-actions-cta button {
    padding: 0.45rem 0.9rem !important;
    font-size: 0.9rem !important;
    width: auto !important; /* shrink to text length */
}
.partner-actions div[data-testid="stVerticalBlock"] > div {
    gap: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# Env and client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# Optional: where Supabase should redirect users after they click the email verification link
# Example: EMAIL_REDIRECT_URL="https://your-deployed-streamlit-app.com"
EMAIL_REDIRECT_URL = os.getenv("EMAIL_REDIRECT_URL", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure Gemini AI
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                "temperature": 0.2,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": 2048,
                # Nudge Gemini to return JSON when requested
                "response_mime_type": "application/json",
            },
        )
    except Exception as e:
        st.warning(f"⚠️ Failed to configure Gemini AI: {e}")
        gemini_model = None
else:
    gemini_model = None

# Configure Groq client (optional)
groq_client = None
if GROQ_API_KEY and Groq is not None:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as _:
        groq_client = None

# Lenient JSON parsing helpers (module-level)
import re as _re_glob
import json as _json_glob
def _strip_fences_glob(txt: str) -> str:
    if txt and txt.strip().startswith("```"):
        return _re_glob.sub(r"^```(?:json)?\n|```$", "", txt.strip(), flags=_re_glob.IGNORECASE)
    return txt
def _normalize_quotes_glob(txt: str) -> str:
    return (txt or "") \
        .replace("\u201c", '"').replace("\u201d", '"') \
        .replace("\u2018", "'").replace("\u2019", "'") \
        .replace(""", '"').replace(""", '"') \
        .replace("'", "'").replace("'", "'")
def _remove_trailing_commas_glob(txt: str) -> str:
    return _re_glob.sub(r",\s*(?=[}\]])", "", txt or "")
def _first_json_object_glob(txt: str) -> str | None:
    m = _re_glob.search(r"\{[\s\S]*\}", txt or "")
    return m.group(0) if m else None
def _parse_lenient_json(raw_text: str):
    if not raw_text:
        return None
    txt = _strip_fences_glob(raw_text)
    txt = _normalize_quotes_glob(txt)
    try:
        return _json_glob.loads(txt)
    except Exception:
        pass
    obj = _first_json_object_glob(txt)
    if obj:
        try:
            return _json_glob.loads(obj)
        except Exception:
            try:
                return _json_glob.loads(_remove_trailing_commas_glob(obj))
            except Exception:
                return None
    try:
        return _json_glob.loads(_remove_trailing_commas_glob(txt))
    except Exception:
        return None

# Simple email sanitizer/validator
def _sanitize_email(raw_email: str) -> str:
    try:
        e = (raw_email or "").strip().lower()
        return e
    except Exception:
        return raw_email or ""
def _is_valid_email(raw_email: str) -> bool:
    try:
        import re as _re_email
        e = (raw_email or "").strip()
        # Basic RFC-ish pattern; good enough for UI validation
        return bool(_re_email.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", e))
    except Exception:
        return False

# Attempt to restore auth session if present
if "sb_session" in st.session_state:
    try:
        supabase.auth.set_session(
            st.session_state["sb_session"].get("access_token"),
            st.session_state["sb_session"].get("refresh_token"),
        )
    except Exception:
        pass

# Auth UI mode (login/signup)
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# ---------- Strict Auth Gate (login required for any access) ----------
def _render_login_screen():
    # Full width login container with logo and title aligned
    st.markdown("""
    <div class="wide-login-container fade-in-up">
        <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; background: rgba(255, 255, 255, 0.95); padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);">
            <div style="flex-shrink: 0;">
                <img src="data:image/png;base64,{}" style="width: clamp(80px, 40vw, 160px); height: auto; display: block; object-fit: contain;" alt="LeanChems Logo">
            </div>
            <div style="flex: 1 1 240px; min-width: 0;">
                <h1 style="margin-bottom: 0.5rem; background: linear-gradient(145deg, #93c5fd, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: clamp(1.4rem, 5vw, 2.4rem);">Leanchems</h1>
                <h2 style="margin: 0; color: #1e40af; font-size: clamp(1rem, 3.5vw, 1.8rem); font-weight: 600;">Product Management System</h2>
            </div>
        </div>
        <p style="margin-top: 1rem; font-size: 1.1rem; text-align: center;">Sign in to access your dashboard</p>
    </div>
    """.format(_get_logo_base64()), unsafe_allow_html=True)
    
    # Auth forms
    if st.session_state.get("auth_mode") == "signup":
        # Signup form
        with st.form("signup_form_full", clear_on_submit=False):
            su_email = st.text_input("📧 Email Address", placeholder="you@example.com")
            su_password = st.text_input("🔐 Password", type="password", placeholder="Create a password")
            su_password2 = st.text_input("🔐 Confirm Password", type="password", placeholder="Re-enter your password")
            st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
            su_submit = st.form_submit_button("✨ Create Account", use_container_width=False, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Already have an account? Sign in", type="secondary"):
            st.session_state["auth_mode"] = "login"
            st.rerun()

        if su_submit:
            su_email_s = _sanitize_email(su_email)
            if not su_email_s or not su_password or not su_password2:
                st.error("🚫 Please fill in all fields")
            elif not _is_valid_email(su_email_s):
                st.error("🚫 Please enter a valid email address")
            elif su_password != su_password2:
                st.error("🚫 Passwords do not match")
            elif len(su_password) < 6:
                st.error("🚫 Password must be at least 6 characters")
            else:
                with st.spinner("📝 Creating your account..."):
                    try:
                        # Request email verification with (optionally) a redirect URL back to this app
                        payload = {"email": su_email_s, "password": su_password}
                        if EMAIL_REDIRECT_URL:
                            payload["options"] = {"email_redirect_to": EMAIL_REDIRECT_URL}
                        resp = supabase.auth.sign_up(payload)
                        # Ask Supabase to send a magic sign-in link as part of verification flow
                        try:
                            if EMAIL_REDIRECT_URL:
                                supabase.auth.resend({
                                    "type": "signup",
                                    "email": su_email_s,
                                    "options": {"email_redirect_to": EMAIL_REDIRECT_URL}
                                })
                            else:
                                supabase.auth.resend({
                                    "type": "signup",
                                    "email": su_email_s,
                                })
                        except Exception:
                            pass
                        st.success("✅ Account created. Please check your email for a verification link. After verifying, use the emailed sign-in link or return here to sign in.")
                        st.info("If you don't see the email, check spam. You can also click 'Resend verification email' below.")
                        st.session_state["pending_verify_email"] = su_email_s
                        st.session_state["auth_mode"] = "login"
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Sign up failed: {e}")
    else:
        # Default: Show login form
        with st.form("login_form_full", clear_on_submit=False):
            email = st.text_input("📧 Email Address", placeholder="you@example.com")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter your password")
            st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
            submit = st.form_submit_button("🚀 Sign In", use_container_width=False, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        # Switch to signup
        if st.button("Create an account", type="secondary"):
            st.session_state["auth_mode"] = "signup"
            st.rerun()
        
        if submit:
            email_s = _sanitize_email(email)
            if not email_s or not password:
                st.error("🚫 Please enter both email and password")
            elif not _is_valid_email(email_s):
                st.error("🚫 Please enter a valid email address")
            else:
                with st.spinner("🔐 Authenticating..."):
                    try:
                        resp = supabase.auth.sign_in_with_password({
                            "email": email_s,
                            "password": password
                        })
                        if resp and resp.user and resp.session:
                            # Set the session state variables that the app expects
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = email_s
                            st.session_state["user_name"] = resp.user.user_metadata.get("name", email_s.split("@")[0])
                            
                            # Set the Supabase user and session data
                            user_role = ((resp.user.user_metadata or {}).get("role") if hasattr(resp.user, "user_metadata") else None) or "viewer"
                            st.session_state["sb_user"] = {
                                "id": resp.user.id,
                                "email": resp.user.email,
                                "role": user_role,
                            }
                            st.session_state["sb_session"] = {
                                "access_token": resp.session.access_token,
                                "refresh_token": resp.session.refresh_token,
                            }
                            
                            st.success("✅ Login successful! Redirecting...")
                            st.rerun()
                        else:
                            st.error("❌ Invalid login response")
                    except Exception as e:
                        st.error(f"❌ Login failed: {e}")

        # Offer to resend verification email when returning to login after signup
        if st.session_state.get("pending_verify_email"):
            pending_email = _sanitize_email(st.session_state.get("pending_verify_email"))
            st.caption(f"A verification email was sent to {pending_email}. Not received?")
            if st.button("Resend verification email", type="secondary"):
                try:
                    if EMAIL_REDIRECT_URL:
                        supabase.auth.resend({
                            "type": "signup",
                            "email": pending_email,
                            "options": {"email_redirect_to": EMAIL_REDIRECT_URL}
                        })
                    else:
                        supabase.auth.resend({
                            "type": "signup",
                            "email": pending_email,
                        })
                    st.success("✅ Verification email resent.")
                except Exception as e:
                    st.error(f"❌ Failed to resend verification email: {e}")
    
    # System description with three key points
    st.markdown("""
    <div style="margin-top: 3rem; padding: 2rem; background: rgba(255, 255, 255, 0.95); border-radius: 15px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);">
        <h3 style="text-align: center; color: #1e40af; margin-bottom: 1.5rem; font-size: 1.4rem; font-weight: 600;">What Our System Does</h3>
        <div style="display: grid; grid-template-columns: 1fr; gap: 1.5rem; max-width: 600px; margin: 0 auto;">
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(147, 197, 253, 0.1); border-radius: 10px; border-left: 4px solid #60a5fa;">
                <div style="font-size: 1.5rem;">🤖</div>
                <div>
                    <h4 style="margin: 0 0 0.25rem 0; color: #1e40af; font-size: 1.1rem; font-weight: 600;">AI-Powered Chemical Intelligence</h4>
                    <p style="margin: 0; color: #4b5563; font-size: 0.95rem;">Advanced AI algorithms for comprehensive chemical data analysis and master data management</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(147, 197, 253, 0.1); border-radius: 10px; border-left: 4px solid #60a5fa;">
                <div style="font-size: 1.5rem;">🔗</div>
                <div>
                    <h4 style="margin: 0 0 0.25rem 0; color: #1e40af; font-size: 1.1rem; font-weight: 600;">Strategic Sourcing Solutions</h4>
                    <p style="margin: 0; color: #4b5563; font-size: 0.95rem;">Comprehensive supplier management and sourcing optimization for chemical procurement</p>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 1rem; padding: 1rem; background: rgba(147, 197, 253, 0.1); border-radius: 10px; border-left: 4px solid #60a5fa;">
                <div style="font-size: 1.5rem;">🗺️</div>
                <div>
                    <h4 style="margin: 0 0 0.25rem 0; color: #1e40af; font-size: 1.1rem; font-weight: 600;">Market Intelligence & Mapping</h4>
                    <p style="margin: 0; color: #4b5563; font-size: 0.95rem;">Real-time market analysis and competitive intelligence for informed decision-making</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; color: #718096; font-size: 0.875rem;">
        <p>🔒 Secure authentication powered by Supabase</p>
    </div>
    """, unsafe_allow_html=True)

def _require_login():
    if not st.session_state.get("sb_user"):
        _render_login_screen()
        st.stop()

# Branding and Auth
# Local logo file - use absolute path for reliability
LEAN_CHEMS_LOGO_URL = os.path.join(os.path.dirname(__file__), "leanchems_logo.png")

def _get_logo_base64():
    """Convert logo image to base64 for embedding in HTML"""
    try:
        if LEAN_CHEMS_LOGO_URL and os.path.exists(LEAN_CHEMS_LOGO_URL):
            with open(LEAN_CHEMS_LOGO_URL, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        else:
            # Return a placeholder if logo doesn't exist
            return ""
    except Exception as e:
        st.error(f"Error loading logo: {e}")
        return ""

MANAGER_EMAILS = {e.strip().lower() for e in (os.getenv("MANAGER_EMAILS", "").split(",")) if e.strip()}
MANAGER_DOMAIN = (os.getenv("MANAGER_DOMAIN") or "").strip().lower()

def get_manager_emails_from_db() -> set:
    try:
        res = supabase.table("managers").select("email").execute()
        emails = { (row.get("email") or "").strip().lower() for row in (res.data or []) if row.get("email") }
        return emails
    except Exception:
        return set()

# Enforce login before rendering any content
_require_login()

# Enhanced Header Section - Wider Layout
st.markdown('<div class="header-container fade-in-up">', unsafe_allow_html=True)

# Main header content in wider columns
col_title, col_user = st.columns([3, 1])
with col_title:
    st.markdown('''
    <div style="text-align: center;">
        <h1 style="margin-bottom: 0.5rem; background: linear-gradient(145deg, #93c5fd, #60a5fa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 1.9rem;">Leanchems Product Management System</h1>
        <p style="color: #718096; margin: 0; font-size: 1rem;">Comprehensive Chemical & Product Data Management</p>
    </div>
    ''', unsafe_allow_html=True)
    
with col_user:
    sb_user = st.session_state.get("sb_user")
    _email_lc = (sb_user.get('email') or '').lower()
    _role = (sb_user.get('role') or '').lower()
    # Check if user is in managers table
    db_manager_emails = get_manager_emails_from_db()
    _is_mgr_display = (
        (_role in {"manager", "admin"})
        or (_email_lc in MANAGER_EMAILS)
        or (_email_lc in db_manager_emails)
        or (_email_lc == "daniel@leanchems.com")
        or (_email_lc == "alhadi@leanchems.com")
    )
    _role_text = "Manager" if _is_mgr_display else "Viewer"
    
    st.markdown(f'''
    <div style="text-align: right; padding: 1rem;">
        <div style="color: #4a5568; font-weight: 600; margin-bottom: 0.5rem;">
            👤 {sb_user.get('email')}
        </div>
        <div style="color: #718096; font-size: 0.875rem; margin-bottom: 1rem;">
            🎭 {_role_text}
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    if st.button("Sign Out", type="secondary", use_container_width=True):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        for k in ["sb_user", "sb_session"]:
            st.session_state.pop(k, None)
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# Derived access flags
sb_user = st.session_state.get("sb_user")
user_role = (sb_user or {}).get("role", "viewer")
user_email = ((sb_user or {}).get("email") or "").strip().lower()

# Role-based access control constants
CHEMICAL_MASTER_ACCESS = {
    "daniel@leanchems.com",
    "bettyabay@leanchems.com", 
    "alhadi@leanchems.com"
}

SOURCING_MASTER_ACCESS = {
    "iman@leanchems.com",
    "meraf@leanchems.com", 
    "alhadi@leanchems.com",
    "bettyabay@leanchems.com",
    "daniel@leanchems.com"
}

def has_chemical_master_access(user_email: str) -> bool:
    """Check if user has access to Chemical Master Data"""
    if not user_email:
        return False
    user_email_lower = user_email.strip().lower()
    return user_email_lower in CHEMICAL_MASTER_ACCESS

def has_sourcing_master_access(user_email: str) -> bool:
    """Check if user has access to Sourcing Master Data"""
    if not user_email:
        return False
    user_email_lower = user_email.strip().lower()
    return user_email_lower in SOURCING_MASTER_ACCESS

def get_user_access_levels(user_email: str) -> dict:
    """Get user's access levels for different modules"""
    if not user_email:
        return {
            "chemical": False,
            "sourcing": False,
            "leanchem": False,
            "market": False
        }
    
    user_email_lower = user_email.strip().lower()
    
    # bettyabay@leanchems.com, daniel@leanchems.com and alhadi@leanchems.com have access to all functions
    if user_email_lower in {"bettyabay@leanchems.com", "daniel@leanchems.com", "alhadi@leanchems.com"}:
        return {
            "chemical": True,
            "sourcing": True,
            "leanchem": True,
            "market": True
        }
    
    return {
        "chemical": has_chemical_master_access(user_email),
        "sourcing": has_sourcing_master_access(user_email),
        "leanchem": True,  # All users can access LeanChem Products
        "market": True      # All users can access Market Data
    }

# User Access Information Display
if user_email:
    user_access = get_user_access_levels(user_email)
    access_info = []
    if user_access["chemical"]:
        access_info.append("Chemical Master Data")
    if user_access["sourcing"]:
        access_info.append("Sourcing Master Data")
        # Also expose sourcing-linked modules when sourcing access is granted
        access_info.append("Partner Master Data")
        access_info.append("Pricing & Costing Master Data")
    if user_access["leanchem"]:
        access_info.append("LeanChem Products")
    if user_access["market"]:
        access_info.append("Market Master Data")
    
    if access_info:
        st.info(f"🔐 **Access Granted:** You have access to: {', '.join(access_info)}")
    else:
        st.warning("⚠️ **No Access:** You don't have access to any modules. Please contact your administrator.")

# Aggregate manager sources: role metadata, env allowlist, optional domain, and managers table
db_manager_emails = get_manager_emails_from_db()
is_manager = False
if user_role in {"manager", "admin"}:
    is_manager = True
elif user_email and (user_email in (MANAGER_EMAILS or set()) or user_email in {"daniel@leanchems.com", "alhadi@leanchems.com"}):
    is_manager = True
elif MANAGER_DOMAIN and user_email.endswith(f"@{MANAGER_DOMAIN}"):
    is_manager = True
elif user_email and user_email in db_manager_emails:
    is_manager = True



# Constants
FIXED_CATEGORIES = [
    "Dry Mix Mortar",
    "Paint & Coating",
    "Admixture",
    "Grinding Aid",
    "Others",
]

COUNTRIES = [
    "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia","Austria",
    "Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan",
    "Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cabo Verde","Cambodia",
    "Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros","Congo","Costa Rica",
    "Croatia","Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt",
    "El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France","Gabon",
    "Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana",
    "Haiti","Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel",
    "Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan","Laos",
    "Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi",
    "Malaysia","Maldives","Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova",
    "Monaco","Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands",
    "New Zealand","Nicaragua","Niger","Nigeria","North Korea","North Macedonia","Norway","Oman","Pakistan","Palau",
    "Palestine","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar","Romania",
    "Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal",
    "Serbia","Seychelles","Sierra Leone","Singapore","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Korea",
    "South Sudan","Spain","Sri Lanka","Sudan","Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan",
    "Tanzania","Thailand","Timor-Leste","Togo","Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu",
    "Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Vatican City",
    "Venezuela","Vietnam","Yemen","Zambia","Zimbabwe"
]

PREDEFINED_TYPES = [
    "RDP",
    "HPMC",
    "SBR",
    "Styrene Acrylic Waterproofing Emulsion",
    "Styrene-Acrylic Binders",
    "Pure Acrylics",
    "Vinyl Acetate-Acrylic",
    "HEC",
    "Iron Oxide",
    "Titanium Dioxide",
    "White Cement",
    "TEA 99%",
    "Domsjoe Lignin DS10 (bigbag)",
    "Polycarboxylate Ether",
    "Sodium Naphthalene Sulfonate Formaldehyde",
    "Sodium Lignosulphonate",
    "Sodium Gluconate",
    "Waterproofing Agent - Penetrol",
]

# In-code Category → Product Types mapping
CATEGORY_TO_TYPES = {
    "Dry Mix Mortar": [
        "RDP",
        "HPMC",
        "SBR",
        "Styrene Acrylic Waterproofing Emulsion",
    ],
    "Paint & Coating": [
        "Iron Oxide",
        "Titanium Dioxide",
        "White Cement",
        "Styrene-Acrylic Binders Emulsion",
        "Pure Acrylic Binders Emulsion",
        "Vinyl Acetate-Acrylic Copolymer Binder",
        "Hydroxyethyl Cellulose (HEC)",
    ],
    "Admixture": [
        "Penetrol Waterproofing Agent",
        "Sodium Gluconate",
        "Sodium Lignosulphonate",
        "Sodium Naphthalene Sulfonate Formaldehyde (SNF)",
        "Polycarboxylate Ether Superplasticizer",
    ],
    "Grinding Aid": [
        "Triethanolamine 99% (TEA)",
        "Domsjö Lignin DS-10 (Sodium Lignosulfonate)"
    ],
    "Others": [],
}

ALLOWED_FILE_EXTS = ["pdf", "docx", "doc", "png", "jpg", "jpeg", "heic", "heif", "webp"]
MAX_FILE_MB = 10

# Excel-driven category/type mapping
CATEGORY_EXCEL_PATH = os.getenv("CATEGORY_EXCEL_PATH", "assets/19 Chemicals - Tax Assessment.xlsx")

# ==========================
# Chemical View Configuration
# ==========================
# Define which fields show in the compact table and detail view for Chemical Master > View
CHEM_VIEW_TABLE_FIELDS: list[tuple[str, str]] = [
    ("generic_name", "Generic Name"),
    ("industry_segments", "Industry Segments"),
    ("functional_categories", "Functional Categories"),
    ("key_applications", "Key Applications"),
    ("family", "Family"),
    ("shelf_life_months", "Shelf Life (months)"),
    ("data_completeness", "Data Completeness"),
]

CHEM_VIEW_DETAIL_FIELDS: list[tuple[str, str]] = [
    ("generic_name", "Generic Name"),
    ("family", "Family"),
    ("synonyms", "Synonyms"),
    ("cas_ids", "CAS IDs"),
    ("hs_codes", "HS Codes"),
    ("industry_segments", "Industry Segments"),
    ("functional_categories", "Functional Categories"),
    ("key_applications", "Key Applications"),
    ("appearance", "Appearance"),
    ("typical_dosage", "Typical Dosage"),
    ("physical_snapshot", "Physical Snapshot"),
    ("compatibilities", "Compatibilities"),
    ("incompatibilities", "Incompatibilities"),
    ("sensitivities", "Sensitivities"),
    ("shelf_life_months", "Shelf Life (months)"),
    ("storage_conditions", "Storage Conditions"),
    ("packaging_options", "Packaging Options"),
    ("summary_80_20", "Summary 80/20"),
    ("summary_technical", "Summary Technical"),
    ("data_completeness", "Data Completeness"),
]

def _format_chem_field(value):
    try:
        if value is None:
            return "-"
        if isinstance(value, list):
            # Pretty-print list of simple values or dicts
            if not value:
                return "-"
            if all(not isinstance(v, (dict, list)) for v in value):
                return ", ".join(str(v) for v in value if str(v).strip()) or "-"
            # Humanize common list-of-dict shapes
            try:
                # hs_codes: [{"region":..., "code":...}]
                if all(isinstance(v, dict) and ("code" in v) for v in value):
                    parts = []
                    for v in value:
                        code = str(v.get("code") or "").strip()
                        region = str(v.get("region") or "").strip()
                        if code and region:
                            parts.append(f"{code} ({region})")
                        elif code:
                            parts.append(code)
                    return ", ".join(parts) if parts else "-"
                # typical_dosage: [{"application":..., "range":...}]
                if all(isinstance(v, dict) and ("application" in v or "range" in v) for v in value):
                    lines = []
                    for v in value:
                        app = str(v.get("application") or "").strip()
                        rng = str(v.get("range") or "").strip()
                        if app and rng:
                            lines.append(f"{app}: {rng}")
                        elif app:
                            lines.append(app)
                        elif rng:
                            lines.append(rng)
                    return "; ".join(lines) if lines else "-"
                # physical_snapshot: [{"name":..., "value":..., "unit":..., "method":...}]
                if all(isinstance(v, dict) and ("name" in v or "value" in v) for v in value):
                    lines = []
                    for v in value:
                        name = str(v.get("name") or "").strip()
                        val = str(v.get("value") or "").strip()
                        unit = str(v.get("unit") or "").strip()
                        method = str(v.get("method") or "").strip()
                        s = name
                        if val and unit:
                            s = f"{name}: {val} {unit}" if name else f"{val} {unit}"
                        elif val:
                            s = f"{name}: {val}" if name else val
                        if method:
                            s = f"{s} ({method})" if s else f"({method})"
                        if s:
                            lines.append(s)
                    return "; ".join(lines) if lines else "-"
            except Exception:
                pass
            # Fallback to JSON for complex lists
            import json as _json_v
            return _json_v.dumps(value, ensure_ascii=False)
        if isinstance(value, (dict,)):
            import json as _json_v
            return _json_v.dumps(value, ensure_ascii=False)
        return str(value)
    except Exception:
        try:
            return str(value)
        except Exception:
            return "-"

def _build_chem_view_rows(records: list[dict], fields: list[tuple[str, str]]) -> list[dict]:
    rows: list[dict] = []
    for rec in records:
        row = {}
        for key, label in fields:
            row[label] = _format_chem_field(rec.get(key))
        rows.append(row)
    return rows

# Global helper: render list/dict values as user-friendly multi-line text
def _ai_list_as_lines(value):
    try:
        import json as _json_for_ai_view
        if isinstance(value, list):
            rendered_lines = []
            for item in value:
                if isinstance(item, dict):
                    parts = []
                    for k, v in item.items():
                        if v is None:
                            continue
                        parts.append(f"{k}: {v}")
                    rendered_lines.append(
                        ", ".join(parts) if parts else _json_for_ai_view.dumps(item, ensure_ascii=False)
                    )
                else:
                    rendered_lines.append(str(item))
            return "\n".join(rendered_lines)
        if value is None:
            return ""
        if isinstance(value, dict):
            return _json_for_ai_view.dumps(value, ensure_ascii=False)
        return str(value)
    except Exception:
        try:
            return str(value)
        except Exception:
            return ""

@st.cache_data
def get_category_type_mapping() -> dict:
    """Return {category: [types...]} from the Excel. Fallback to empty mapping on error."""
    mapping: dict[str, set[str]] = {}
    try:
        import pandas as pd  # type: ignore
        df = pd.read_excel(CATEGORY_EXCEL_PATH)
        cols_lower = {str(c).strip().lower(): c for c in df.columns}
        # Heuristic column names
        cat_col = None
        type_col = None
        for key in ["category", "product category", "category name"]:
            if key in cols_lower:
                cat_col = cols_lower[key]
                break
        for key in ["product type", "type", "product"]:
            if key in cols_lower:
                type_col = cols_lower[key]
                break
        # Fallbacks
        if cat_col is None and len(df.columns) >= 1:
            cat_col = df.columns[0]
        if type_col is None and len(df.columns) >= 2:
            type_col = df.columns[1]
        if cat_col is None or type_col is None:
            return {}
        for _, row in df[[cat_col, type_col]].dropna().iterrows():
            cat = str(row[cat_col]).strip()
            typ = str(row[type_col]).strip()
            if not cat or not typ:
                continue
            mapping.setdefault(cat, set()).add(typ)
        # Convert sets to sorted lists
        return {k: sorted(v) for k, v in mapping.items()}
    except Exception:
        return {}

def validate_product_name(name: str) -> tuple[bool, str]:
    if not name or not name.strip():
        return False, "Product name is required"
    if len(name.strip()) < 3:
        return False, "Product name must be at least 3 characters"
    if len(name.strip()) > 200:
        return False, "Product name must be <= 200 characters"
    return True, ""

def validate_file(uploaded_file) -> tuple[bool, str]:
    if not uploaded_file:
        return True, ""  # optional
    size_ok = uploaded_file.size <= MAX_FILE_MB * 1024 * 1024
    if not size_ok:
        return False, f"File too large. Max {MAX_FILE_MB}MB"
    ext = uploaded_file.name.split(".")[-1].lower()
    if ext not in ALLOWED_FILE_EXTS:
        return False, f"Unsupported file type. Allowed: {', '.join(ALLOWED_FILE_EXTS)}"
    return True, ""

def get_distinct_product_types() -> list[str]:
    try:
        res = supabase.table("chemical_types").select("name").execute()
        values = sorted({(row.get("name") or "").strip() for row in (res.data or []) if row.get("name")})
        return [v for v in values if v]
    except Exception:
        return []

def get_distinct_industry_segments() -> list[str]:
    """Distinct industry segments from Chemical Master Data."""
    try:
        res = supabase.table("chemical_types").select("industry_segments").execute()
        rows = res.data or []
        values: set[str] = set()
        for row in rows:
            segs = row.get("industry_segments") or []
            try:
                for s in segs:
                    s_str = str(s).strip()
                    if s_str:
                        values.add(s_str)
            except Exception:
                continue
        return sorted(values)
    except Exception:
        return []

def get_functional_categories_for_segment(segment: str) -> list[str]:
    """Distinct functional categories for chemicals that belong to a segment."""
    try:
        if not segment:
            return []
        wanted = segment.strip().lower()
        res = supabase.table("chemical_types").select("industry_segments,functional_categories").execute()
        rows = res.data or []
        fc: set[str] = set()
        for row in rows:
            segs = [str(s).strip().lower() for s in (row.get("industry_segments") or []) if str(s).strip()]
            if any(wanted == s or wanted in s for s in segs):
                for c in (row.get("functional_categories") or []):
                    c_str = str(c).strip()
                    if c_str:
                        fc.add(c_str)
        return sorted(fc)
    except Exception:
        return []

def fetch_chemical_types_for_category(category: str) -> list[str]:
    """Deprecated in favor of mapping-based lookup. Kept for compatibility."""
    try:
        return get_types_for_category(category)
    except Exception:
        return []

def get_types_for_category(category: str) -> list[str]:
    """Return product types for a category.

    Priority:
    Only from Chemical Master Data (chemical_types.name where category matches).
    Removes hardcoded and Excel-mapped types so the list reflects saved records only.
    """
    if not category:
        return []
    try:
        res_db = supabase.table("chemical_types").select("name,category").eq("category", category).execute()
        names = []
        for row in (res_db.data or []):
            nm = (row.get("name") or "").strip()
            if nm:
                names.append(nm)
        return sorted(set(names))
    except Exception:
        return []

def upload_tds_to_supabase(uploaded_file, product_id: str):
    if not uploaded_file:
        return None, None, None, None
    ext = uploaded_file.name.split(".")[-1].lower()
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    content_type = content_types.get(ext, "application/octet-stream")
    key = f"tds_files/{product_id}/{uuid.uuid4()}.{ext}"
    supabase.storage.from_("product-documents").upload(
        key,
        uploaded_file.getvalue(),
        {"content-type": content_type, "x-upsert": "true"}
    )
    public_url = f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/public/product-documents/{key}"
    return public_url, uploaded_file.name, uploaded_file.size, ext.upper()

def _storage_key_from_public_url(public_url: str) -> str | None:
    """Extract storage object key from a public URL."""
    try:
        marker = "/storage/v1/object/public/product-documents/"
        if marker in (public_url or ""):
            return public_url.split(marker, 1)[1]
        return None
    except Exception:
        return None

def _delete_storage_object_by_url(public_url: str) -> bool:
    """Best-effort delete of a storage object given its public URL."""
    try:
        key = _storage_key_from_public_url(public_url)
        if not key:
            return False
        supabase.storage.from_("product-documents").remove([key])
        return True
    except Exception:
        return False

def upload_supporting_doc(uploaded_file, tds_id: str):
    if not uploaded_file:
        return None, None, None, None
    ext = uploaded_file.name.split(".")[-1].lower()
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    content_type = content_types.get(ext, "application/octet-stream")
    key = f"supporting_docs/{tds_id}/{uuid.uuid4()}.{ext}"
    supabase.storage.from_("product-documents").upload(
        key,
        uploaded_file.getvalue(),
        {"content-type": content_type, "x-upsert": "true"}
    )
    public_url = f"https://{SUPABASE_URL.split('//')[1]}/storage/v1/object/public/product-documents/{key}"
    return public_url, uploaded_file.name, uploaded_file.size, ext.upper()

# ------------------
# Global session-state reset helpers (used across modules)
# ------------------
def _reset_session_keys(keys: list[str]):
    try:
        for k in keys:
            try:
                st.session_state.pop(k, None)
            except Exception:
                pass
    except Exception:
        pass

def _reset_session_by_prefix(prefixes: list[str]):
    try:
        for k in list(st.session_state.keys()):
            if any(k.startswith(pfx) for pfx in prefixes):
                try:
                    st.session_state.pop(k, None)
                except Exception:
                    pass
    except Exception:
        pass

def _has_unsaved_chemical_changes() -> bool:
    """Check if there are unsaved changes in chemical editing session"""
    try:
        # Check if we're in chemical section and have AI extracted data or form data
        if st.session_state.get("main_section") != "chemical":
            return False
        
        current_tab = st.session_state.get("chemical_current_tab", "Add Chemical")
        
        # Check for unsaved changes in Add Chemical tab
        if current_tab == "Add Chemical":
            # Check for AI extracted data that hasn't been saved
            if st.session_state.get("chem_ai_extracted"):
                return True
                
            # Check for any chemical form data that might indicate editing
            # Exclude navigation and selection keys that don't represent unsaved changes
            excluded_keys = {
                "chem_selected_category", "chem_seg_select", "chem_add_new_seg", "chem_new_seg",
                "chem_current_tab", "chem_manage_refresh_token"
            }
            chem_keys = [k for k in st.session_state.keys() if k.startswith("chem_")]
            if any(k for k in chem_keys if k not in excluded_keys):
                return True
        
        # Check for unsaved changes in Manage Chemicals tab
        elif current_tab == "Manage Chemicals":
            # Check for any chemical manage form data that might indicate editing
            # Look for form keys that start with 'c' followed by the chemical ID (like 'cn_', 'cf_', etc.)
            manage_keys = [k for k in st.session_state.keys() if k.startswith("cn_") or k.startswith("cf_") or k.startswith("csy_") or k.startswith("cca_") or k.startswith("ch_") or k.startswith("cc_") or k.startswith("ci_") or k.startswith("cak_") or k.startswith("cdj_") or k.startswith("cap_") or k.startswith("cps_") or k.startswith("ccom_") or k.startswith("cinc_") or k.startswith("csen_") or k.startswith("csh_") or k.startswith("cst_") or k.startswith("cpa_") or k.startswith("cdc_") or k.startswith("c80_") or k.startswith("cstt_")]
            if manage_keys:
                return True
            
        return False
    except Exception:
        return False

def _clear_chemical_editing_session():
    """Clear all chemical editing related session state"""
    try:
        # Preserve navigation and selection keys
        preserve_keys = {
            "chem_selected_category", "chem_seg_select", "chem_add_new_seg", "chem_new_seg",
            "chem_current_tab", "chem_manage_refresh_token"
        }
        
        keys_to_remove = []
        for key in st.session_state.keys():
            if key.startswith("chem_") and key not in preserve_keys:
                keys_to_remove.append(key)
        
        # Also clear manage form data (keys that start with 'c' followed by underscore and ID)
        for key in st.session_state.keys():
            if (key.startswith("cn_") or key.startswith("cf_") or key.startswith("csy_") or 
                key.startswith("cca_") or key.startswith("ch_") or key.startswith("cc_") or 
                key.startswith("ci_") or key.startswith("cak_") or key.startswith("cdj_") or 
                key.startswith("cap_") or key.startswith("cps_") or key.startswith("ccom_") or 
                key.startswith("cinc_") or key.startswith("csen_") or key.startswith("csh_") or 
                key.startswith("cst_") or key.startswith("cpa_") or key.startswith("cdc_") or 
                key.startswith("c80_") or key.startswith("cstt_")):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
    except Exception:
        pass

def _has_unsaved_changes(module: str) -> bool:
    """Generic function to check for unsaved changes in any module"""
    try:
        if module == "chemical":
            return _has_unsaved_chemical_changes()
        elif module == "sourcing":
            return _has_unsaved_sourcing_changes()
        elif module == "partner_master":
            return _has_unsaved_partner_changes()
        elif module == "pricing":
            return _has_unsaved_pricing_changes()
        return False
    except Exception:
        return False

def _clear_module_session(module: str):
    """Generic function to clear session state for any module"""
    try:
        if module == "chemical":
            _clear_chemical_editing_session()
        elif module == "sourcing":
            _clear_sourcing_session()
        elif module == "partner_master":
            _clear_partner_session()
        elif module == "pricing":
            _clear_pricing_session()
    except Exception:
        pass

def _has_unsaved_sourcing_changes() -> bool:
    """Check if there are unsaved changes in TDS/sourcing session"""
    try:
        if st.session_state.get("main_section") != "sourcing":
            return False
        
        current_section = st.session_state.get("sourcing_section", "add")
        
        # Check for unsaved changes in Add TDS tab
        if current_section == "add":
            # Check for TDS extracted data that hasn't been saved
            if st.session_state.get("extracted_tds_data") or st.session_state.get("extracted_tds_data_norm"):
                return True
                
            # Check for TDS form data that might indicate editing
            excluded_keys = {
                "sourcing_section", "tds_defaults", "tds_hydrate_pending", "category_select_prev"
            }
            tds_keys = [k for k in st.session_state.keys() if k.startswith("tds_")]
            if any(k for k in tds_keys if k not in excluded_keys):
                return True
        
        # Check for unsaved changes in Manage TDS tab
        elif current_section == "manage":
            # Check for any TDS manage form data that might indicate editing
            # Look for form keys that start with 't' followed by the TDS ID (like 'tn_', 'tf_', etc.)
            manage_keys = [k for k in st.session_state.keys() if k.startswith("tn_") or k.startswith("tf_") or k.startswith("ts_") or k.startswith("tp_") or k.startswith("tw_") or k.startswith("th_") or k.startswith("tt_")]
            if manage_keys:
                return True
            
        return False
    except Exception:
        return False

def _clear_sourcing_session():
    """Clear all TDS/sourcing related session state"""
    try:
        # Preserve navigation keys
        preserve_keys = {
            "sourcing_section", "tds_defaults", "tds_hydrate_pending", "category_select_prev"
        }
        
        keys_to_remove = []
        for key in st.session_state.keys():
            if (key.startswith("tds_") or key.startswith("extracted_tds_")) and key not in preserve_keys:
                keys_to_remove.append(key)
        
        # Also clear manage form data (keys that start with 't' followed by underscore and ID)
        for key in st.session_state.keys():
            if (key.startswith("tn_") or key.startswith("tf_") or key.startswith("ts_") or 
                key.startswith("tp_") or key.startswith("tw_") or key.startswith("th_") or 
                key.startswith("tt_")):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
    except Exception:
        pass

def _has_unsaved_partner_changes() -> bool:
    """Check if there are unsaved changes in partner session"""
    try:
        if st.session_state.get("main_section") != "partner_master":
            return False
        
        current_tab = st.session_state.get("partner_current_tab", "Add Partner")
        
        # Check for unsaved changes in Add Partner or Add Chemical tabs
        if current_tab in ["Add Partner", "Add Chemical"]:
            # Check for partner form data that might indicate editing
            excluded_keys = {
                "partner_go_manage", "partner_current_tab"
            }
            partner_keys = [k for k in st.session_state.keys() if k.startswith("partner_") or k.startswith("add_more_")]
            if any(k for k in partner_keys if k not in excluded_keys):
                return True
        
        # Check for unsaved changes in Manage tab
        elif current_tab == "Manage":
            # Check for any partner manage form data that might indicate editing
            # Look for form keys that start with 'p' followed by the partner ID (like 'pn_', 'pc_', etc.)
            manage_keys = [k for k in st.session_state.keys() if k.startswith("pn_") or k.startswith("pc_") or k.startswith("ps_") or k.startswith("pd_")]
            if manage_keys:
                return True
            
        return False
    except Exception:
        return False

def _clear_partner_session():
    """Clear all partner related session state"""
    try:
        # Preserve navigation keys
        preserve_keys = {
            "partner_go_manage", "partner_view_open_id", "partner_current_tab"
        }
        
        keys_to_remove = []
        for key in st.session_state.keys():
            if (key.startswith("partner_") or key.startswith("add_more_")) and key not in preserve_keys:
                keys_to_remove.append(key)
        
        # Also clear manage form data (keys that start with 'p' followed by underscore and ID)
        for key in st.session_state.keys():
            if (key.startswith("pn_") or key.startswith("pc_") or key.startswith("ps_") or 
                key.startswith("pd_")):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
    except Exception:
        pass

def _has_unsaved_pricing_changes() -> bool:
    """Check if there are unsaved changes in pricing session"""
    try:
        if st.session_state.get("main_section") != "pricing":
            return False
        
        current_tab = st.session_state.get("pricing_current_tab", "Add")
        
        # Check for unsaved changes in Add tab
        if current_tab == "Add":
            # Check for pricing form data that might indicate editing
            # Exclude navigation keys
            excluded_keys = {
                "pricing_current_tab", "pricing_prev_partner_label", "pricing_prev_tds_label", 
                "pricing_form_reset_token", "pending_pricing_tab"
            }
            pricing_keys = [k for k in st.session_state.keys() if k.startswith("pricing_") and k not in excluded_keys]
            if pricing_keys:
                return True
            
            # Check for form input keys (like g_0_inc_0, k_0_cu_1, etc.)
            form_keys = [k for k in st.session_state.keys() if any(k.startswith(prefix) for prefix in ["g_", "k_", "o_"]) and any(k.endswith(suffix) for suffix in ["_inc_", "_cu_", "_ce_", "_pu_", "_pe_"])]
            if form_keys:
                return True
        
        # Check for unsaved changes in Manage tab
        elif current_tab == "Manage":
            # Check for any pricing manage form data that might indicate editing
            # Look for form keys that start with 'pm_' (pricing manage)
            manage_keys = [k for k in st.session_state.keys() if k.startswith("pm_")]
            if manage_keys:
                return True
        
        # Check for unsaved changes in View tab
        elif current_tab == "View":
            # Check for any view-related form data that might indicate editing
            view_keys = [k for k in st.session_state.keys() if k.startswith("pv_")]
            if view_keys:
                return True
            
        return False
    except Exception:
        return False

def _clear_pricing_session():
    """Clear all pricing related session state"""
    try:
        # Preserve navigation keys
        preserve_keys = {
            "pricing_current_tab"
        }
        
        keys_to_remove = []
        for key in st.session_state.keys():
            # Clear pricing form data but preserve navigation
            if key.startswith("pricing_") and key not in preserve_keys:
                keys_to_remove.append(key)
            
            # Clear manage form data (keys that start with 'pm_')
            if key.startswith("pm_"):
                keys_to_remove.append(key)
            
            # Clear view form data (keys that start with 'pv_')
            if key.startswith("pv_"):
                keys_to_remove.append(key)
            
            # Clear form input keys (like g_0_inc_0, k_0_cu_1, etc.)
            if any(key.startswith(prefix) for prefix in ["g_", "k_", "o_"]) and any(key.endswith(suffix) for suffix in ["_inc_", "_cu_", "_ce_", "_pu_", "_pe_"]):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            st.session_state.pop(key, None)
    except Exception:
        pass


def _is_in_manage_tab(module: str) -> bool:
    """Check if user is currently in a manage tab"""
    try:
        if module == "chemical":
            current_tab = st.session_state.get("chemical_current_tab", "Add Chemical")
            return current_tab == "Manage Chemicals"
        elif module == "sourcing":
            current_section = st.session_state.get("sourcing_section", "add")
            return current_section == "manage"
        elif module == "partner_master":
            current_tab = st.session_state.get("partner_current_tab", "Add Partner")
            return current_tab == "Manage"
        elif module == "pricing":
            current_tab = st.session_state.get("pricing_current_tab", "Add")
            return current_tab == "Manage"
        return False
    except Exception:
        return False

def name_exists(name: str) -> bool:
    res = supabase.table("chemical_types").select("id").eq("name", name.strip()).limit(1).execute()
    return bool(res.data)

def _resolve_chemical_type_id(type_name: str, category: str) -> str | None:
    try:
        t = (type_name or "").strip()
        if not t:
            return None
        query = supabase.table("chemical_types").select("id,name,category").eq("name", t)
        if category:
            query = query.eq("category", category)
        res = query.limit(1).execute()
        rows = res.data or []
        if rows:
            return rows[0].get("id")
    except Exception:
        pass
    return None

def _split_brand_grade(trade: str) -> tuple[str | None, str | None]:
    try:
        s = (trade or "").strip()
        if not s:
            return None, None
        # Heuristic: first token brand, remainder grade
        parts = s.split(None, 1)
        if len(parts) == 1:
            return parts[0], None
        return parts[0], parts[1]
    except Exception:
        return None, None

def create_tds_sourcing_entity(*, chemical_type_id: str | None, brand: str | None, grade: str | None, owner: str | None, source: str | None, specs: dict | None, metadata: dict | None):
    try:
        payload = {
            "id": str(uuid.uuid4()),
            "chemical_type_id": chemical_type_id,
            "brand": brand or None,
            "grade": grade or None,
            "owner": owner or None,
            "source": source or None,
            "specs": specs or {},
            "metadata": metadata or {},
        }
        supabase.table("tds_data").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, str(e)

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file (PDF, DOCX, or image)"""
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
            
        elif file_extension in ['docx', 'doc']:
            # Extract text from DOCX
            doc = Document(io.BytesIO(uploaded_file.getvalue()))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
            
        elif file_extension in ['png', 'jpg', 'jpeg', 'heic', 'heif', 'webp']:
            # For images, we'll need to use OCR or send to Gemini Vision
            # For now, return a placeholder - you can implement OCR here
            return "Image file detected. OCR processing needed."
            
        else:
            return "Unsupported file format"
            
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_tds_info_with_ai(text_content):
    """Use Gemini AI to extract TDS information from text content"""
    if not gemini_model:
        return None
    
    try:
        prompt = f"""
        Extract the following information from this Technical Data Sheet (TDS) text. 
        Return the information in a structured format. If any information is not found, return "Not found".

        Text content:
        {text_content}

        Please extract and return ONLY the following information in this exact format:
        - Generic Product Name: [extract generic product name]
        - Trade Name: [extract trade name or model name]
        - Supplier Name: [extract supplier or manufacturer name]
        - Packaging Size & Type: [extract packaging information]
        - Net Weight: [extract net weight]
        - Technical Specification: [extract key technical specifications]

        Format your response exactly like this example:
        Generic Product Name: Redispersible Polymer Powder
        Trade Name: VINNAPAS® 5010N
        Supplier Name: Wacker Chemie AG
        Packaging Size & Type: 25kg bags
        Net Weight: 25kg
        HS Code: 3904.30.00
        Technical Specification: Vinyl acetate-ethylene copolymer, solid content 99%, particle size <1mm
        """
        
        response = gemini_model.generate_content(prompt)

        # Robustly extract text from candidates, handling safety blocks
        def _response_to_text(resp) -> str:
            try:
                candidates = getattr(resp, "candidates", None) or []
                # Prefer first non-blocked candidate with content parts
                for cand in candidates:
                    # finish_reason may be enum/int/string; treat 2 or name=="SAFETY" as blocked
                    fr = getattr(cand, "finish_reason", None)
                    fr_name = getattr(fr, "name", None)
                    if str(fr).strip() == "2" or (fr_name and fr_name.upper() == "SAFETY"):
                        continue
                    content = getattr(cand, "content", None)
                    parts = getattr(content, "parts", None) or []
                    texts = []
                    for p in parts:
                        t = getattr(p, "text", None)
                        if isinstance(t, str):
                            texts.append(t)
                    if texts:
                        return "\n".join(texts).strip()
                # Fallback to top-level text accessor if available
                try:
                    return (getattr(resp, "text", "") or "").strip()
                except Exception:
                    return ""
            except Exception:
                return ""

        raw_text = _response_to_text(response)
        if not raw_text:
            # Retry with a safer, shorter prompt and truncated content to avoid safety blocks
            safe_text = (text_content or "")[:5000]
            retry_prompt = f"""
            You are extracting neutral catalog metadata from a Technical Data Sheet. Respond with JSON only.
            Text content (truncated):\n{safe_text}
            Return a single JSON object with keys: ["Generic Product Name","Trade Name","Supplier Name","Packaging Size & Type","Net Weight","HS Code","Technical Specification"].
            Use empty strings where unknown.
            """
            try:
                retry_resp = gemini_model.generate_content(retry_prompt)
                raw_text = _response_to_text(retry_resp)
            except Exception:
                raw_text = ""
        if not raw_text:
            st.warning("⚠️ AI response was blocked or empty. Please try another file or smaller excerpt.")
            return None
        
        # Prefer JSON parsing when possible
        parsed_json = _parse_lenient_json(raw_text)
        if isinstance(parsed_json, dict):
            return parsed_json

        # Fallback: parse "Key: Value" lines
        extracted_info = {}
        if raw_text:
            lines = raw_text.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key:
                        extracted_info[key] = value
        return extracted_info
         
    except Exception as e:
        st.error(f"AI extraction error: {str(e)}")
        st.info("💡 This could be due to content filtering, network issues, or API limits. You can still manually fill in the fields below.")
        return None

def process_tds_with_ai(uploaded_file):
    """Process TDS file with AI to extract information"""
    if not uploaded_file:
        return None
    
    # Show processing status
    with st.spinner("🤖 AI is analyzing the TDS file..."):
        # Extract text from file
        text_content = extract_text_from_file(uploaded_file)
        
        if text_content and text_content != "Unsupported file format" and not text_content.startswith("Error"):
            # Use AI to extract information
            extracted_info = extract_tds_info_with_ai(text_content)
            return extracted_info
        else:
            st.error(f"Could not extract text from file: {text_content}")
            return None

# Enhanced Navigation Section
st.markdown('<div style="margin: 2rem 0;">', unsafe_allow_html=True)
st.markdown('''
<div style="text-align: center; margin-bottom: 2rem;">
    <h3 style="color: #4a5568; font-weight: 600; margin-bottom: 0.5rem;"> Select Module</h3>
    <p style="color: #718096; font-size: 0.9rem; margin: 0;">Choose a module to begin managing your data</p>
</div>
''', unsafe_allow_html=True)

if "main_section" not in st.session_state:
    st.session_state["main_section"] = None

# Navigation Cards with Icons and Descriptions
# Get user access levels
user_access = get_user_access_levels(user_email)

# Filter navigation items based on user access
nav_items = [
    {
        "key": "chemical",
        "title": "🧪 Chemical Master Data",
        "subtitle": "Chemical Database",
        "description": "Manage chemical properties, specifications & classifications",
        "icon": "🧪",
        "access": user_access["chemical"]
    },
    {
        "key": "sourcing", 
        "title": "📋 TDS Master Data",
        "subtitle": "TDS Management",
        "description": "Handle Technical Data Sheets & supplier information",
        "icon": "📋",
        "access": user_access["sourcing"]
    },
    {
        "key": "partner_master",
        "title": "🤝 Partner Master Data",
        "subtitle": "Business partner",
        "description": "Manage partners linked to TDS records",
        "icon": "🤝",
        "access": user_access["sourcing"]
    },
    {
        "key": "pricing",
        "title": "💵 Pricing & Costing Master Data",
        "subtitle": "Pricing & Costing",
        "description": "Maintain partner/TDS pricing and costing by incoterm",
        "icon": "💵",
        "access": user_access["sourcing"]
    },
    {
        "key": "leanchem",
        "title": "🏢 LeanChem Products",
        "subtitle": "Product Portfolio",
        "description": "Manage Leanchems proprietary product catalog",
        "icon": "🏢",
        "access": user_access["leanchem"]
    },
    {
        "key": "market",
        "title": "📊 Market Master Data",
        "subtitle": "Market Intelligence", 
        "description": "Track market trends & competitive analysis",
        "icon": "📊",
        "access": user_access["market"]
    }
]

# Filter out items user doesn't have access to
accessible_nav_items = [item for item in nav_items if item["access"]]

# Adjust column layout based on number of accessible items
if len(accessible_nav_items) > 0:
    nav_cols = st.columns(len(accessible_nav_items))
    # Wrap buttons in a container to scope equal-size CSS
    st.markdown('<div class="nav-buttons">', unsafe_allow_html=True)
    
    for i, item in enumerate(accessible_nav_items):
        with nav_cols[i]:
            # Check if this section is active
            is_active = st.session_state.get("main_section") == item["key"]
            active_class = "active" if is_active else ""
            
            # Create clickable card
            button_clicked = st.button(
                f"""{item["icon"]} {item["title"].split(' ', 1)[1]}""",
                key=f"nav_{item['key']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            )
            
            # Add description below button
            st.markdown(f'''
            <div style="text-align: center; margin-top: 0.5rem; padding: 0 0.5rem;">
                <small style="color: #718096; font-size: 0.8rem; line-height: 1.3;">
                    {item["description"]}
                </small>
            </div>
            ''', unsafe_allow_html=True)
            
            if button_clicked:
                # Check for unsaved changes in current module before navigation
                current_module = st.session_state.get("main_section")
                if current_module and _has_unsaved_changes(current_module):
                    st.session_state["pending_navigation"] = item["key"]
                    st.session_state["show_navigation_confirm"] = True
                    st.rerun()
                else:
                    # Clear current module session and navigate
                    if current_module:
                        _clear_module_session(current_module)
                    st.session_state["main_section"] = item["key"]
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("You don't have access to any modules. Please contact your administrator.")

st.markdown('</div>', unsafe_allow_html=True)

# Navigation confirmation dialog for unsaved changes
if st.session_state.get("show_navigation_confirm", False):
    current_module = st.session_state.get("main_section")
    module_names = {
        "chemical": "Chemical Master Data",
        "sourcing": "TDS Master Data", 
        "partner_master": "Partner Master Data",
        "pricing": "Pricing & Costing Master Data"
    }
    module_name = module_names.get(current_module, "Current Module")
    is_manage_tab = _is_in_manage_tab(current_module)
    
    st.markdown('<div class="form-card" style="border: 2px solid #f56565; background-color: #fed7d7;">', unsafe_allow_html=True)
    
    if is_manage_tab:
        st.warning(f"⚠️ You have unsaved changes in {module_name} Manage section")
        st.markdown("You have unsaved changes that will be lost if you navigate away. Please save your changes using the individual 'Save' buttons for each record, then navigate.")
        st.info("💡 **Tip**: Each record in the manage section has its own 'Save' button. Save all your changes first, then navigate.")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Discard & Continue", key="nav_discard_continue", type="primary"):
                # Clear session and navigate
                if current_module:
                    _clear_module_session(current_module)
                st.session_state["show_navigation_confirm"] = False
                pending_nav = st.session_state.pop("pending_navigation", None)
                if pending_nav:
                    st.session_state["main_section"] = pending_nav
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="nav_cancel"):
                # Cancel navigation and stay in current section
                st.session_state["show_navigation_confirm"] = False
                st.session_state.pop("pending_navigation", None)
                st.rerun()
        
        with col3:
            st.caption("Your unsaved changes will be lost if you continue.")
    else:
        st.warning(f"⚠️ You have unsaved changes in {module_name}")
        st.markdown("You have unsaved changes that will be lost if you navigate away. What would you like to do?")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("🗑️ Discard & Continue", key="nav_discard_continue", type="primary"):
                # Clear session and navigate
                if current_module:
                    _clear_module_session(current_module)
                st.session_state["show_navigation_confirm"] = False
                pending_nav = st.session_state.pop("pending_navigation", None)
                if pending_nav:
                    st.session_state["main_section"] = pending_nav
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="nav_cancel"):
                # Cancel navigation and stay in current section
                st.session_state["show_navigation_confirm"] = False
                st.session_state.pop("pending_navigation", None)
                st.rerun()
        
        with col3:
            st.caption("Your unsaved changes will be lost if you continue.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Access control messages for restricted sections
if st.session_state.get("main_section") == "chemical" and not has_chemical_master_access(user_email):
    st.error("🚫 Access Denied: You don't have permission to access Chemical Master Data. This module is restricted to Daniel and Betty Abay.")
    st.info("Please contact your administrator if you believe you should have access to this module.")
    st.stop()

if st.session_state.get("main_section") == "sourcing" and not has_sourcing_master_access(user_email):
    st.error("🚫 Access Denied: You don't have permission to access Sourcing Master Data. This module is restricted to Iman, Meraf, Alhadi, and Betty Abay.")
    st.info("Please contact your administrator if you believe you should have access to this module.")
    st.stop()

# Access control for Partner Master Data
if st.session_state.get("main_section") == "partner_master" and not has_sourcing_master_access(user_email):
    st.error("🚫 Access Denied: You don't have permission to access Partner Master Data. This module is restricted to Iman, Meraf, Alhadi, and Betty Abay.")
    st.info("Please contact your administrator if you believe you should have access to this module.")
    st.stop()

# Enhanced Sourcing sub-navigation when active
if st.session_state.get("main_section") == "sourcing" and has_sourcing_master_access(user_email):
    st.markdown('<div class="form-card" style="margin: 2rem 0;">', unsafe_allow_html=True)
    st.markdown('''
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h3 style="color: #4a5568; font-weight: 600; margin-bottom: 0.5rem;">TDS Master Data</h3>
        <p style="color: #718096; font-size: 0.9rem; margin: 0;">Technical Data Sheet Management</p>
    </div>
    ''', unsafe_allow_html=True)
    
    if "sourcing_section" not in st.session_state:
        st.session_state["sourcing_section"] = "add"
    
    sub_cols = st.columns(3)
    sub_nav_items = [
        {"key": "add", "icon": "➕", "title": "Add TDS", "desc": "Upload new technical data sheets"},
        {"key": "manage", "icon": "⚙️", "title": "Manage TDS", "desc": "Edit and organize existing TDS"},
        {"key": "view", "icon": "👁️", "title": "View TDS", "desc": "Browse and search TDS library"}
    ]
    
    for i, item in enumerate(sub_nav_items):
        with sub_cols[i]:
            is_active = st.session_state.get("sourcing_section") == item["key"]
            
            if st.button(
                f"""{item["icon"]} {item["title"]}""",
                key=f"sub_nav_{item['key']}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                # Check for unsaved changes when switching tabs within sourcing
                current_section = st.session_state.get("sourcing_section")
                if (current_section != item["key"] and current_section and _has_unsaved_sourcing_changes()):
                    # Set pending navigation instead of showing dialog immediately
                    st.session_state["pending_sourcing_section"] = item["key"]
                    st.rerun()
                else:
                    st.session_state["sourcing_section"] = item["key"]
                    st.rerun()
            
            st.markdown(f'''
            <div style="text-align: center; margin-top: 0.5rem;">
                <small style="color: #718096; font-size: 0.8rem;">
                    {item["desc"]}
                </small>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Handle pending TDS section changes with confirmation dialog
    if st.session_state.get("pending_sourcing_section"):
        new_section = st.session_state.get("pending_sourcing_section")
        current_section = st.session_state.get("sourcing_section")
        
        if current_section == "add":
            st.warning("⚠️ You have unsaved changes in the Add TDS tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_tds_add", type="primary"):
                    _clear_sourcing_session()
                    st.session_state["sourcing_section"] = new_section
                    st.session_state.pop("pending_sourcing_section")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_tds_add"):
                    st.session_state.pop("pending_sourcing_section")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif current_section == "manage":
            st.warning("⚠️ You have unsaved changes in the Manage TDS tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_tds_manage", type="primary"):
                    _clear_sourcing_session()
                    st.session_state["sourcing_section"] = new_section
                    st.session_state.pop("pending_sourcing_section")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_tds_manage"):
                    st.session_state.pop("pending_sourcing_section")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()

# UI - Add Product
if st.session_state.get("main_section") == "sourcing" and st.session_state.get("sourcing_section") == "add" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Add TDS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.container():
        st.subheader("Basic Information")
        # Category select (selection only; no add) with placeholder
        _cat_placeholder = "— Select —"
        _cat_options = [_cat_placeholder] + FIXED_CATEGORIES
        _category_sel = st.selectbox(
            "Chemical Category *",
            _cat_options,
            key="category_select"
        )
        category = "" if _category_sel == _cat_placeholder else _category_sel
        # Reset type controls when category changes
        prev_cat = st.session_state.get("category_select_prev")
        if prev_cat != category:
            if prev_cat:
                prev_key_base = (prev_cat or 'none').replace(' ', '_').replace('&', 'and')
                prev_type_checkbox_key = f"add_new_type_{prev_key_base}"
                prev_type_select_key = f"type_select_{prev_key_base}"
                prev_type_input_key = f"new_type_name_{prev_key_base}"
                st.session_state.pop(prev_type_checkbox_key, None)
                st.session_state.pop(prev_type_select_key, None)
                st.session_state.pop(prev_type_input_key, None)
            st.session_state["category_select_prev"] = category
            # Force a rerun so dependent widgets refresh their options for the new category
            st.rerun()

        # Product Type filtered by selected category (selection only; no add)
        existing_types = get_types_for_category(category)
        type_options = existing_types
        if type_options:
            _type_placeholder = "— Select —"
            _type_opts = [_type_placeholder] + type_options
            _type_sel = st.selectbox(
                "Product Type *",
                options=_type_opts,
                key=f"type_select_{(category or 'none').replace(' ', '_').replace('&', 'and')}"
            )
            selected_type = "" if _type_sel == _type_placeholder else _type_sel
        else:
            st.info("No mapped product types for this category in Chemical Master Data.")
            selected_type = ""

        # Product Code after selecting category and type
        name = st.text_input("Product Code *", placeholder="Unique product code", key="tds_product_code")

        description = st.text_area("Description", placeholder="Optional description", height=100, key="tds_description")

        st.markdown("---")
        st.subheader("Product Status")
        _yn_placeholder = "— Select —"
        _yn_sel = st.selectbox(
            "Is it Leanchems legacy/existing/coming product?",
            [_yn_placeholder, "Yes", "No"],
            index=0,
            key="tds_product_status"
        )
        is_leanchems_product = None if _yn_sel == _yn_placeholder else _yn_sel

        st.markdown("---")
        st.subheader("Source of TDS")
        _src_placeholder = "— Select —"
        _src_sel = st.selectbox(
            "Where did the TDS come from?",
            [_src_placeholder, "Supplier", "Customer", "Competitor"],
            index=0,
            key="tds_source_select"
        )
        tds_source = None if _src_sel == _src_placeholder else _src_sel

        st.markdown("---")
        st.subheader("Technical Data Sheet (TDS)")
        st.warning("⚠️ TDS upload is required. Products cannot be saved without a TDS file.")
        # Single file picker only (mobile-friendly)
        # Reset-aware file uploader (tokenized key so it fully clears after save)
        _tds_file_token = st.session_state.get("tds_file_reset_token", "0")
        uploaded_file = st.file_uploader(
            "Upload TDS (PDF/DOCX/Images) — max 10MB *",
            type=ALLOWED_FILE_EXTS,
            key=f"tds_file_picker_{_tds_file_token}",
            accept_multiple_files=False,
            help="Tip: On mobile, choose 'Files' or 'Browse' to pick from device storage."
        )

        # AI Processing Button (single source)
        if uploaded_file and gemini_model:
            col_ai_process1, col_ai_process2 = st.columns([1, 3])
            with col_ai_process1:
                if st.button("🤖 Extract with AI", type="secondary"):
                    extracted_data = process_tds_with_ai(uploaded_file)
                    if extracted_data:
                        # Normalize keys robustly (case/space/punctuation variations)
                        import re as _re_norm_keys
                        def _normalize_key(s: str) -> str:
                            ns = str(s or "").strip().lower()
                            ns = ns.replace("&", " and ")
                            ns = ns.replace("-", "_")
                            ns = ns.replace(" ", "_")
                            ns = ns.replace("\u2013", "_").replace("\u2014", "_")
                            ns = ns.replace('"', '').replace("'", "")
                            ns = _re_norm_keys.sub(r"[^a-z0-9_]+", "", ns)
                            return ns
                        norm = { _normalize_key(k): v for k, v in extracted_data.items() }
                        st.session_state["extracted_tds_data"] = extracted_data
                        st.session_state["extracted_tds_data_norm"] = norm
                        st.session_state["tds_hydrate_pending"] = True
                        st.success("✅ AI extraction completed!")
                        st.rerun()
                    else:
                        st.error("❌ AI extraction failed. Please check your file.")
            with col_ai_process2:
                if st.session_state.get("extracted_tds_data"):
                    st.success("AI data extracted and ready to use!")

        st.markdown("---")
        st.subheader("AI Product Management System – TDS Information Extraction")
        if gemini_model:
            st.info("🤖 AI will automatically extract information from the uploaded TDS file")
        else:
            st.warning("⚠️ Gemini AI not configured. Please set GEMINI_API_KEY in your environment variables.")

        # (Debug section removed)
        
        # AI TDS Information Extraction fields
        # One-time hydration after an extract click
        def _ensure_hydrated():
            _n = st.session_state.get("extracted_tds_data_norm") or {}
            if not _n and st.session_state.get("extracted_tds_data"):
                # Build norm from legacy stored dict
                _tmp = st.session_state.get("extracted_tds_data") or {}
                import re as _re_norm_keys
                def _normalize_key(s: str) -> str:
                    ns = str(s or "").strip().lower()
                    ns = ns.replace("&", " and ")
                    ns = ns.replace("-", "_")
                    ns = ns.replace(" ", "_")
                    ns = ns.replace("\u2013", "_").replace("\u2014", "_")
                    ns = ns.replace('"', '').replace("'", "")
                    ns = _re_norm_keys.sub(r"[^a-z0-9_]+", "", ns)
                    return ns
                _n = {_normalize_key(k): v for k, v in _tmp.items()}
                st.session_state["extracted_tds_data_norm"] = _n
            if not _n:
                st.stop()
            def _get_first(keys: list[str], default: str = ""):
                for k in keys:
                    if k in _n and _n.get(k):
                        return _n.get(k)
                return default
            # Store hydrated defaults in a separate dict to avoid widget key conflicts
            st.session_state["tds_defaults"] = {
                "generic_product_name": _get_first(["generic_product_name","generic_name","genericproductname"]) or "",
                "trade_name": _get_first(["trade_name","model_name","tradename","modelname"]) or "",
                "supplier_name": _get_first(["supplier_name","manufacturer","suppliername"]) or "",
                # Include common normalized variants including double-underscore from " & " replacement
                "packaging_size_type": _get_first([
                    "packaging_size_type",
                    "packaging_size_and_type",
                    "packagingsizeandtype",
                    "packaging_size__and__type",
                    "packaging_sizeandtype",
                    "packaging_and_type",
                    "packaging",
                    "packaging_size"
                ]) or "",
                "net_weight": _get_first(["net_weight","netweight","weight"]) or "",
                "hs_code": _get_first(["hs_code","hscode","hs"]) or "",
                "technical_specification": _get_first(["technical_specification","technical_specs","technicalspecification","technicalspecs","specification","specifications"]) or "",
            }

        if st.session_state.get("tds_hydrate_pending"):
            _ensure_hydrated()
            st.session_state["tds_hydrate_pending"] = False
        else:
            # Also hydrate opportunistically if fields are empty but we have extracted data
            if st.session_state.get("extracted_tds_data") and not st.session_state.get("tds_defaults"):
                _ensure_hydrated()

        col_ai1, col_ai2 = st.columns(2)
        _norm_vals = st.session_state.get("extracted_tds_data_norm") or {}
        
        with col_ai1:
            _tds_defs = st.session_state.get("tds_defaults") or {}
            generic_product_name = st.text_input(
                "Generic Product Name",
                value=_tds_defs.get("generic_product_name") or _norm_vals.get("generic_product_name", ""),
                placeholder="AI extracted generic name",
                key="tds_generic_name"
            )
            trade_name = st.text_input(
                "Trade Name (Model Name)", 
                value=_tds_defs.get("trade_name") or _norm_vals.get("trade_name", ""),
                placeholder="AI extracted trade/model name",
                key="tds_trade_name"
            )
            supplier_name = st.text_input(
                "Supplier Name", 
                value=_tds_defs.get("supplier_name") or _norm_vals.get("supplier_name", ""),
                placeholder="AI extracted supplier name",
                key="tds_supplier_name"
            )
            # Resolve value from defaults or normalized key variants
            _pkg_val = _tds_defs.get("packaging_size_type")
            if not _pkg_val:
                for _k in [
                    "packaging_size_type",
                    "packaging_size_and_type",
                    "packagingsizeandtype",
                    "packaging_size__and__type",
                    "packaging_sizeandtype",
                    "packaging_and_type",
                    "packaging",
                    "packaging_size",
                ]:
                    if _norm_vals.get(_k):
                        _pkg_val = _norm_vals.get(_k)
                        break
            packaging_size_type = st.text_input(
                "Packaging Size & Type", 
                value=_pkg_val or "",
                placeholder="AI extracted packaging info",
                key="tds_packaging"
            )
        with col_ai2:
            net_weight = st.text_input(
                "Net Weight", 
                value=_tds_defs.get("net_weight") or _norm_vals.get("net_weight", ""),
                placeholder="AI extracted weight",
                key="tds_net_weight"
            )
            # HS Code input removed; use AI-extracted/default value silently
            hs_code = _tds_defs.get("hs_code") or _norm_vals.get("hs_code", "")
            technical_spec = st.text_area(
                "Technical Specification", 
                value=_tds_defs.get("technical_specification") or _norm_vals.get("technical_specification", ""),
                placeholder="AI extracted technical specifications", 
                height=100,
                key="tds_tech_spec"
            )



        submitted = st.button("Save Record", type="primary")

    if submitted:
        # Validate name
        ok, msg = validate_product_name(name)
        if not ok:
            st.error(msg)
        elif not category:
            st.error("Category is required. Select a category or enter a new one.")
        elif name_exists(name):
            st.error("A product with this name already exists")
        elif not selected_type:
            st.error("Product Type is required. Select a type or enter a new one.")
        elif not uploaded_file:
            st.error("TDS file is required. Please upload a TDS file before saving the product.")
        else:
            # Validate file
            source_file = uploaded_file
            f_ok, f_msg = validate_file(source_file)
            if not f_ok:
                st.error(f_msg)
            else:
                try:
                    # Create a placeholder ID to use for storage path
                    product_id = str(uuid.uuid4())

                    # Upload TDS if provided
                    tds_url, tds_name, tds_size, tds_type = upload_tds_to_supabase(source_file, product_id)

                    # Save everything to tds_data table only
                    # First, find or create the chemical type
                    try:
                        # Try to find existing chemical type
                        existing_type = supabase.table("chemical_types").select("id").eq("name", selected_type.strip()).eq("category", category).limit(1).execute()
                        if existing_type.data:
                            chem_type_id = existing_type.data[0]["id"]
                        else:
                            # Create new chemical type if it doesn't exist
                            new_type_payload = {
                        "id": product_id,
                                "name": selected_type.strip(),
                        "category": category,
                            }
                            supabase.table("chemical_types").insert(new_type_payload).execute()
                            chem_type_id = product_id
                    except Exception as e:
                        st.error(f"Failed to handle chemical type: {e}")
                        st.stop()
                    brand, grade = _split_brand_grade(trade_name)
                    
                    # Build specs (actual technical specifications from TDS)
                    specs = {}
                    if technical_spec:
                        specs["technical_specification"] = technical_spec
                    if hs_code:
                        specs["hs_code"] = hs_code
                    if net_weight:
                        specs["net_weight"] = net_weight
                    
                    # Build metadata (ALL TDS information goes here)
                    metadata = {
                        # Product info
                        "product_name": name.strip(),
                        "product_type": selected_type.strip(),
                        "category": category,
                        "is_leanchems_product": is_leanchems_product,
                        "is_active": True,
                        # TDS extracted info
                        "generic_product_name": (generic_product_name or None),
                        "trade_name": (trade_name or None),
                        "supplier_name": (supplier_name or None),
                        "packaging_size_type": (packaging_size_type or None),
                        # Duplicate important fields for UI rendering (also stored in specs)
                        "net_weight": (net_weight or None),
                        "technical_spec": (technical_spec or None),
                        "description": (description or None),
                        # TDS file info
                        "tds_file_url": tds_url,
                        "tds_file_name": tds_name,
                        "tds_file_size": tds_size,
                        "tds_file_type": tds_type,
                        "tds_source": tds_source,
                    }
                    
                    # Create tds_data entry
                    ok_entity, err_entity = create_tds_sourcing_entity(
                        chemical_type_id=chem_type_id,
                        brand=(brand or supplier_name or None),
                        grade=grade,
                        owner=tds_source,  # Supplier / Customer / Competitor
                        source="TDS Upload",  # Where it came from
                        specs=specs,
                        metadata=metadata,
                    )
                    if not ok_entity:
                        st.warning(f"Saved product, but failed to create sourcing entity: {err_entity}")
                    st.success("✅ Record saved successfully")
                    # Clear Add TDS session artifacts and reset the form for a fresh insert
                    try:
                        for k in [
                            "extracted_tds_data",
                            "extracted_tds_data_norm",
                            "tds_defaults",
                            "tds_hydrate_pending",
                            # old file uploader key (prior versions)
                            "tds_file_picker",
                            "category_select_prev",
                            # Explicit keys for Add TDS widgets
                            "tds_product_code",
                            "tds_description",
                            "tds_product_status",
                            "tds_source_select",
                            # Explicit input widget keys used in Add TDS
                            "tds_generic_name",
                            "tds_trade_name",
                            "tds_supplier_name",
                            "tds_packaging",
                            "tds_net_weight",
                            "tds_hs_code",
                            "tds_tech_spec",
                            # Selection keys
                            "category_select",
                        ]:
                            st.session_state.pop(k, None)
                        # Also clear dynamic type select key for the selected category if exists
                        try:
                            _cat = category or st.session_state.get("category_select_prev") or ""
                            if _cat:
                                _key_base = (_cat or 'none').replace(' ', '_').replace('&', 'and')
                                st.session_state.pop(f"type_select_{_key_base}", None)
                        except Exception:
                            pass
                        # Bump file-uploader token so Streamlit remounts the widget (clears selected file)
                        try:
                            st.session_state["tds_file_reset_token"] = str(uuid.uuid4())
                        except Exception:
                            pass
                        # Explicitly reset key widget values back to placeholders/empty
                        try:
                            st.session_state["category_select"] = "— Select —"
                        except Exception:
                            pass
                        try:
                            st.session_state["tds_product_code"] = ""
                            st.session_state["tds_description"] = ""
                            st.session_state["tds_product_status"] = "— Select —"
                            st.session_state["tds_source_select"] = "— Select —"
                        except Exception:
                            pass

                        # Stay in Add tab with a fresh/empty form
                        st.session_state["sourcing_section"] = "add"
                    except Exception:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save product: {e}")
        
        # Add clear session button if there are unsaved changes

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# Chemical Master Data: Helpers
# ==========================

def normalize_chemical_name(raw_name: str) -> str:
    return (raw_name or "").strip()

def chemical_name_exists(name: str) -> bool:
    try:
        n = normalize_chemical_name(name)
        if not n:
            return False
        res = supabase.table("chemical_types").select("id").eq("generic_name", n).limit(1).execute()
        return bool(res.data)
    except Exception:
        return False

def search_chemicals_by_name(query: str) -> list[dict]:
    try:
        q = (query or "").strip()
        if not q:
            return []
        # Case-insensitive partial match when available
        try:
            res = supabase.table("chemical_types").select("id,name,applications,spec_template,metadata,hs_code,category").ilike("name", f"%{q}%").limit(10).execute()
        except Exception:
            # Fallback: exact match only
            res = supabase.table("chemical_types").select("id,name,applications,spec_template,metadata,hs_code,category").eq("name", q).limit(10).execute()
        rows = res.data or []
        return [_map_type_record_to_legacy(r) for r in rows]
    except Exception:
        return []

def _map_type_record_to_legacy(rec: dict) -> dict:
    try:
        meta = rec.get("metadata") or {}
        spec = rec.get("spec_template") or {}
        out = {
            **rec,
            # legacy keys synthesized from new schema
            "generic_name": rec.get("name"),
            "family": meta.get("family"),
            "synonyms": meta.get("synonyms") or [],
            "cas_ids": meta.get("cas_ids") or [],
            "key_applications": rec.get("applications") or [],
            "typical_dosage": spec.get("typical_dosage") or [],
            "physical_snapshot": spec.get("physical_snapshot") or [],
            # pull-throughs from metadata for compatibility
            "industry_segments": meta.get("industry_segments") or [],
            "functional_categories": meta.get("functional_categories") or [],
            "appearance": meta.get("appearance"),
            "compatibilities": meta.get("compatibilities") or [],
            "incompatibilities": meta.get("incompatibilities") or [],
            "sensitivities": meta.get("sensitivities") or [],
            "storage_conditions": meta.get("storage_conditions"),
            "packaging_options": meta.get("packaging_options") or [],
            "summary_80_20": meta.get("summary_80_20"),
            "summary_technical": meta.get("summary_technical"),
            "data_completeness": meta.get("data_completeness", rec.get("data_completeness")),
            # ensure shelf life is visible in legacy dict
            "shelf_life_months": rec.get("shelf_life_months") if rec.get("shelf_life_months") is not None else meta.get("shelf_life_months"),
            # hs_codes: prefer metadata; else derive from core hs_code column if present
            "hs_codes": (meta.get("hs_codes") or ([{"region": "WCO", "code": rec.get("hs_code")}]
                           if rec.get("hs_code") else [])),
        }
        return out
    except Exception:
        return rec

def fetch_chemicals() -> list[dict]:
    try:
        # First attempt: ordered by name
        query = supabase.table("chemical_types").select("*")
        try:
            res = query.order("name").execute()
            data = res.data or []
            data = [_map_type_record_to_legacy(r) for r in data]
            try:
                st.session_state["chem_fetch_meta"] = {
                    "count": len(data),
                    "ordered": True,
                    "error": getattr(res, "error", None),
                }
            except Exception:
                pass
            return data
        except Exception:
            # Fallback: fetch without order in case ordering causes an error
            res2 = query.execute()
            data2 = res2.data or []
            data2 = [_map_type_record_to_legacy(r) for r in data2]
            try:
                st.session_state["chem_fetch_meta"] = {
                    "count": len(data2),
                    "ordered": False,
                    "error": getattr(res2, "error", None),
                }
            except Exception:
                pass
            return data2
    except Exception as e:
        st.error(f"Failed to fetch chemicals: {e}")
        # Final fallback: return empty list
        return []

def _map_ui_payload_to_type_record(ui: dict) -> dict:
    try:
        # Core fields per 80/20 schema
        name = (ui.get("generic_name") or "").strip()
        category = st.session_state.get("chem_selected_category") or None
        # hs_code: take first code if available
        hs_codes = ui.get("hs_codes") or []
        hs_code = None
        try:
            if isinstance(hs_codes, list) and hs_codes:
                first = hs_codes[0]
                if isinstance(first, dict):
                    hs_code = (first.get("code") or None)
                else:
                    hs_code = str(first)
        except Exception:
            hs_code = None
        applications = ui.get("key_applications") or []
        # spec_template: keep meaningful structure if available
        spec_template = {
            "typical_dosage": ui.get("typical_dosage") or [],
            "physical_snapshot": ui.get("physical_snapshot") or [],
        }
        # metadata: catch-all of remaining fields
        metadata = {k: v for k, v in ui.items() if k not in {"generic_name","hs_codes","key_applications","typical_dosage","physical_snapshot"}}
        return {
            "id": ui.get("id") or None,
            "name": name or None,
            "category": category,
            "hs_code": hs_code,
            "applications": applications if isinstance(applications, list) else [],
            "spec_template": spec_template,
            "metadata": metadata,
        }
    except Exception:
        # Fallback: store everything in metadata
        return {
            "name": (ui.get("generic_name") or None),
            "metadata": ui,
        }

def create_chemical(ui_payload: dict):
    type_rec = _map_ui_payload_to_type_record(ui_payload)
    # Remove None id to let DB default generate
    if not type_rec.get("id"):
        type_rec.pop("id", None)
    return supabase.table("chemical_types").insert(type_rec).execute()

def update_chemical(chemical_id: str, updates: dict):
    # Merge strategy: update core columns when present; push everything into metadata as well
    type_updates = {}
    ui_map = _map_ui_payload_to_type_record({**updates, "id": chemical_id})
    for key in ["name","category","hs_code","applications","spec_template"]:
        if ui_map.get(key) is not None:
            type_updates[key] = ui_map[key]
    # Merge metadata: fetch current then merge
    try:
        curr = supabase.table("chemical_types").select("metadata").eq("id", chemical_id).limit(1).execute()
        curr_meta = ((curr.data or [{}])[0] or {}).get("metadata") or {}
    except Exception:
        curr_meta = {}
    new_meta = {**curr_meta, **ui_map.get("metadata", {})}
    type_updates["metadata"] = new_meta
    return supabase.table("chemical_types").update(type_updates).eq("id", chemical_id).execute()

def delete_chemical(chemical_id: str):
    return supabase.table("chemical_types").delete().eq("id", chemical_id).execute()

def analyze_chemical_with_ai(chemical_name: str) -> dict | None:
    if not gemini_model:
        # If Gemini is not configured, we can still use Groq if available
        pass
    name = (chemical_name or "").strip()
    if not name:
        return None
    try:
        # Helper to normalize output to our 20-field schema
        def _normalize(data: dict) -> dict:
            import re as _re_norm
            from typing import Any, List, Dict
            def as_text(value) -> str:
                if value is None:
                    return ""
                if isinstance(value, str):
                    return value
                try:
                    # Prefer JSON for complex types to avoid lossy cast
                    return _json_glob.dumps(value, ensure_ascii=False)
                except Exception:
                    return str(value)
            def parse_int_safe(value) -> int:
                if value is None:
                    return 0
                if isinstance(value, (int, float)):
                    try:
                        return int(value)
                    except Exception:
                        return 0
                s = str(value)
                m = _re_norm.search(r"-?\d+", s)
                return int(m.group(0)) if m else 0
            def parse_float_safe(value) -> float:
                if value is None:
                    return 0.0
                if isinstance(value, (int, float)):
                    try:
                        return float(value)
                    except Exception:
                        return 0.0
                s = str(value).strip().lower()
                # map qualitative to numeric
                if s in {"high", "high confidence"}:
                    return 0.9
                if s in {"medium", "moderate"}:
                    return 0.5
                if s in {"low", "poor"}:
                    return 0.2
                # percentage like '85%'
                m = _re_norm.search(r"-?\d+(?:\.\d+)?", s)
                if m:
                    try:
                        v = float(m.group(0))
                        # if looks like percentage >1, scale to 0..1
                        return v/100.0 if v > 1.0 else v
                    except Exception:
                        return 0.0
                return 0.0
            def ensure_list(value):
                if value is None:
                    return []
                if isinstance(value, list):
                    return value
                if isinstance(value, str):
                    return [s.strip() for s in value.split(",") if s.strip()]
                return []
            def ensure_list_of_dicts(value: Any) -> List[Dict]:
                if value is None:
                    return []
                if isinstance(value, list):
                    return [v for v in value if isinstance(v, dict)]
                if isinstance(value, dict):
                    return [value]
                if isinstance(value, str):
                    # Try lenient JSON parse
                    parsed = _parse_lenient_json(value)
                    if isinstance(parsed, list):
                        return [v for v in parsed if isinstance(v, dict)]
                    if isinstance(parsed, dict):
                        return [parsed]
                    # Try simple "k: v, k: v" parser for one line
                    entry: Dict[str, Any] = {}
                    for pair in [p for p in value.split(",") if ":" in p]:
                        k, v = pair.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if k:
                            entry[k] = v
                    return [entry] if entry else []
                return []
            def normalize_hs_codes(value: Any) -> List[Dict]:
                # Accept list of dicts, single dict, list of strings, or single string
                lst = ensure_list_of_dicts(value)
                if lst:
                    return lst
                if isinstance(value, list):
                    items = []
                    for v in value:
                        s = str(v).strip()
                        if s:
                            items.append({"region": "WCO", "code": s})
                    return items
                if isinstance(value, str):
                    s = value.strip()
                    return ([{"region": "WCO", "code": s}] if s else [])
                return []
            def get_first(data_obj: Dict, candidates: List[str]):
                # Case/space/underscore-insensitive get
                norm_map = {str(k).replace(" ", "").replace("_", "").lower(): k for k in data_obj.keys()}
                for c in candidates:
                    key = norm_map.get(str(c).replace(" ", "").replace("_", "").lower())
                    if key is not None:
                        return data_obj.get(key)
                return None
            normalized = {
                "generic_name": as_text(data.get("generic_name") or name).strip(),
                "family": as_text(data.get("family") or "").strip(),
                "synonyms": ensure_list(data.get("synonyms")),
                "cas_ids": ensure_list(data.get("cas_ids")),
                "hs_codes": normalize_hs_codes(data.get("hs_codes")),
                "functional_categories": ensure_list(data.get("functional_categories")),
                "industry_segments": ensure_list(data.get("industry_segments")),
                "key_applications": ensure_list(data.get("key_applications")),
                "typical_dosage": ensure_list_of_dicts(
                    get_first(data, ["typical_dosage", "typical dosage", "dosage", "usage_range", "usage"]) or data.get("typical_dosage")
                ),
                "appearance": as_text(data.get("appearance") or "").strip(),
                "physical_snapshot": ensure_list_of_dicts(
                    get_first(data, ["physical_snapshot", "physical properties", "physical_properties", "properties", "key_properties"]) or data.get("physical_snapshot")
                ),
                "compatibilities": ensure_list(data.get("compatibilities")),
                "incompatibilities": ensure_list(data.get("incompatibilities")),
                "sensitivities": ensure_list(data.get("sensitivities")),
                "shelf_life_months": parse_int_safe(data.get("shelf_life_months")),
                "storage_conditions": as_text(data.get("storage_conditions") or "").strip(),
                "packaging_options": ensure_list(data.get("packaging_options")),
                "summary_80_20": as_text(data.get("summary_80_20") or "").strip(),
                "summary_technical": as_text(data.get("summary_technical") or "").strip(),
                "data_completeness": parse_float_safe(data.get("data_completeness")),
            }
            dc = normalized["data_completeness"]
            if dc < 0.0:
                normalized["data_completeness"] = 0.0
            elif dc > 1.0:
                normalized["data_completeness"] = 1.0
            return normalized

        # 1) Try Groq first if available
        if groq_client is not None:
            try:
                groq_schema_prompt = f"""
You are assisting with business-safe catalog metadata for a material. Respond with valid JSON only.
Material: "{name}"

IMPORTANT: Pay special attention to these key fields:
- cas_ids: Extract CAS registry numbers (format XXX-XX-X or XXXXXXX-XX-X). Common examples:
  * Sodium Chloride: 7647-14-5
  * Acetic Acid: 64-19-7
  * Ethanol: 64-17-5
  * Water: 7732-18-5
  * Sulfuric Acid: 7664-93-9
- physical_snapshot: Extract measurable physical properties like density, melting point, boiling point, viscosity, pH, etc.
- typical_dosage: Extract typical usage amounts, concentrations, or application rates

Required JSON schema keys (arrays can be empty):
{{
  "generic_name": string,
  "family": string,
  "synonyms": array,
  "cas_ids": array, // CAS registry numbers in format XXX-XX-X - MUST include if known
  "hs_codes": array,  // of objects like {{"region":"WCO","code":"HS"}}
  "functional_categories": array,
  "industry_segments": array,
  "key_applications": array,
  "typical_dosage": array, // of objects like {{"application":"use case","range":"concentration or amount"}}
  "appearance": string,
  "physical_snapshot": array, // of objects like {{"name":"property name","value":"numerical value","unit":"unit","method":"test method"}}
  "compatibilities": array,
  "incompatibilities": array,
  "sensitivities": array,
  "shelf_life_months": number,
  "storage_conditions": string,
  "packaging_options": array,
  "summary_80_20": string,
  "summary_technical": string,
  "data_completeness": number
}}
"""
                chat = groq_client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that outputs valid JSON only."},
                        {"role": "user", "content": groq_schema_prompt},
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    max_tokens=1200,
                )
                raw = (chat.choices[0].message.content or "").strip()
                if raw:
                    groq_data = _parse_lenient_json(raw)
                    if groq_data and isinstance(groq_data, dict):
                        norm = _normalize(groq_data)
                        try:
                            st.session_state["chem_ai_source"] = "groq"
                        except Exception:
                            pass
                        return norm
            except Exception:
                # Fall through to Gemini
                pass

        # 2) Fallback to Gemini if available
        if gemini_model is None:
            return None
        prompt_primary = f"""
 You are creating neutral catalog metadata for a material. Provide general, non-hazardous, business-safe descriptions only.
 Do not provide procedures, handling instructions, or dangerous guidance. Output valid JSON only matching the schema.
 
 Material: "{name}"
 
 IMPORTANT: Pay special attention to extracting these key fields:
 - cas_ids: Look for CAS registry numbers (format: XXX-XX-X or XXXXXXX-XX-X). Common examples:
   * Sodium Chloride: 7647-14-5
   * Acetic Acid: 64-19-7
   * Ethanol: 64-17-5
   * Water: 7732-18-5
   * Sulfuric Acid: 7664-93-9
 - physical_snapshot: Extract measurable physical properties like density, melting point, boiling point, viscosity, pH, etc.
 - typical_dosage: Extract typical usage amounts, concentrations, or application rates
 
 Schema:
 {{
   "generic_name": "{name}",
   "family": "material type",
   "synonyms": ["alternative names"],
   "cas_ids": ["CAS numbers - look for format XXX-XX-X - MUST include if known"],
   "hs_codes": [{{"region": "WCO", "code": "HS code"}}],
   "functional_categories": ["primary functions"],
   "industry_segments": ["main industries"],
   "key_applications": ["primary uses"],
   "typical_dosage": [{{"application": "use case", "range": "concentration or amount range"}}],
   "appearance": "brief physical description",
   "physical_snapshot": [{{"name": "property name", "value": "numerical value", "unit": "unit of measurement", "method": "test method if known"}}],
   "compatibilities": ["compatible systems"],
   "incompatibilities": ["incompatible systems"],
   "sensitivities": ["environmental factors"],
   "shelf_life_months": 24,
   "storage_conditions": "storage requirements",
   "packaging_options": ["packaging types"],
   "summary_80_20": "one-sentence description",
   "summary_technical": "concise technical description",
   "data_completeness": 0.8
 }}
 """

        def _try_generate_text(p):
            try:
                r = gemini_model.generate_content(p)
                if not r:
                    return None
                if hasattr(r, 'finish_reason') and r.finish_reason in (2, 3, 4):
                    return None
                try:
                    txt = (r.text or "").strip()
                    # Remove code fences to improve downstream parsing
                    txt = _strip_fences_glob(txt)
                except Exception:
                    return None
                return txt if txt else None
            except Exception:
                return None

        raw = _try_generate_text(prompt_primary)
        if not raw:
            st.warning("⚠️ AI response was blocked or empty.")
            return None
        try:
            st.session_state["chem_ai_last_raw"] = raw
        except Exception:
            pass
        # Try full-text JSON, then embedded JSON object
        data = _parse_lenient_json(raw)
        if not data or not isinstance(data, dict):
            # Strict retry: ask for JSON-only, same keys
            prompt_retry = f"""
Return a single valid JSON object only. No prose, no code fences. Use empty strings or empty arrays where unknown.

IMPORTANT: Focus on extracting:
- cas_ids: CAS registry numbers (format XXX-XX-X). Examples: Sodium Chloride: 7647-14-5, Acetic Acid: 64-19-7, Ethanol: 64-17-5
- physical_snapshot: Physical properties with name, value, unit, method
- typical_dosage: Usage amounts/concentrations with application and range

Keys: ["generic_name","family","synonyms","cas_ids","hs_codes","functional_categories","industry_segments","key_applications","typical_dosage","appearance","physical_snapshot","compatibilities","incompatibilities","sensitivities","shelf_life_months","storage_conditions","packaging_options","summary_80_20","summary_technical","data_completeness"].
Material: "{name}"
"""
            raw_retry = _try_generate_text(prompt_retry)
            if raw_retry:
                try:
                    st.session_state["chem_ai_last_raw"] = raw_retry
                except Exception:
                    pass
                data = _parse_lenient_json(raw_retry)
            if not data or not isinstance(data, dict):
                # Final fallback: parse key: value lines heuristically
                def _kv_lines_to_dict(txt: str) -> Dict[str, Any]:
                    out: Dict[str, Any] = {}
                    for line in (txt or "").splitlines():
                        if ":" not in line:
                            continue
                        k, v = line.split(":", 1)
                        k = k.strip().lower()
                        v = v.strip()
                        if not k:
                            continue
                        out[k] = v
                    return out
                parsed = _kv_lines_to_dict(raw or raw_retry or "")
                if not parsed:
                    st.warning("⚠️ Could not parse AI response as JSON: No JSON object found.")
                    # Return minimal object so UI can still proceed
                    return _normalize({"generic_name": name})
                # Map common synonyms to our schema before normalize
                synonym_map = {
                    "name": "generic_name",
                    "generic product name": "generic_name",
                    "generic name": "generic_name",
                    "trade name": "synonyms",
                    "applications": "key_applications",
                    "uses": "key_applications",
                    "use cases": "key_applications",
                    "industry": "industry_segments",
                    "industry segments": "industry_segments",
                    "functional categories": "functional_categories",
                    "family": "family",
                    "appearance": "appearance",
                    "storage": "storage_conditions",
                    "storage conditions": "storage_conditions",
                    "summary": "summary_80_20",
                    "technical summary": "summary_technical",
                    "hs code": "hs_codes",
                    "hs codes": "hs_codes",
                    "cas": "cas_ids",
                    "cas ids": "cas_ids",
                }
                mapped: Dict[str, Any] = {"generic_name": name}
                for k, v in parsed.items():
                    key = synonym_map.get(k, k)
                    if key in {"synonyms","cas_ids","functional_categories","industry_segments","key_applications","packaging_options","compatibilities","incompatibilities","sensitivities"}:
                        mapped[key] = [s.strip() for s in v.split(",") if s.strip()]
                    elif key == "hs_codes":
                        codes = [s.strip() for s in v.split(",") if s.strip()]
                        mapped[key] = [{"region": "WCO", "code": c} for c in codes]
                    elif key == "shelf_life_months":
                        mapped[key] = v
                    else:
                        mapped[key] = v
                return _normalize(mapped)
        return _normalize(data)
    except Exception as e:
        st.error(f"AI analysis error: {e}")
        st.info("💡 This could be due to content filtering, network issues, or API limits. You can still manually fill in the fields below.")
        return None

# Helpers for Manage
def fetch_products():
    try:
        res = supabase.table("chemical_types").select("*").order("category").order("name").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to fetch products: {e}")
        return []

def fetch_tds_data():
    """Fetch TDS data from tds_data table"""
    try:
        res = supabase.table("tds_data").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to fetch TDS data: {e}")
        return []

def update_product(product_id: str, updates: dict):
    return supabase.table("chemical_types").update(updates).eq("id", product_id).execute()

def name_exists_other(name: str, current_id: str) -> bool:
    res = supabase.table("chemical_types").select("id").eq("name", name.strip()).neq("id", current_id).limit(1).execute()
    return bool(res.data)



def build_version_entry(prod, updates):
    from datetime import datetime
    changed = {k: updates.get(k) for k in updates.keys()}
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "changed": changed
    }
    history = prod.get("version_history") or []
    history.append(entry)
    return history

# UI - Manage Products
if st.session_state.get("main_section") == "sourcing" and st.session_state.get("sourcing_section") == "manage" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Manage TDS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # Authorization: only managers can access Manage tab
    if not sb_user:
        st.info("Please sign in to access Manage Products.")
    elif not is_manager:
        if not st.session_state.get("user_name"):
            pass
        st.error("You do not have permission to access Manage Products.")
    else:
        # Enhanced Filters
        st.subheader("📊 Filter TDS Records")
        colf1, colf2, colf3 = st.columns([2, 2, 2])
        with colf1:
            filter_category = st.selectbox("Filter by Category", ["All"] + FIXED_CATEGORIES)
        with colf2:
            # Brand Filter
            all_brands = []
            try:
                res = supabase.table("tds_data").select("brand").execute()
                all_brands = sorted(list(set([row.get("brand") for row in (res.data or []) if row.get("brand")])))
            except Exception:
                pass
            filter_brand = st.selectbox("Filter by Brand", ["All"] + all_brands)
        with colf3:
            # Owner Filter
            filter_owner = st.selectbox("Filter by Owner", ["All", "Supplier", "Customer", "Competitor"])

        # Search filter
        search = st.text_input("Search by product name/brand/supplier", placeholder="Start typing...")

        tds_records = fetch_tds_data()
        # Apply enhanced filters
        filtered = []
        for tds in tds_records:
            metadata = tds.get("metadata", {})
            # Category filter
            if filter_category != "All" and metadata.get("category") != filter_category:
                continue
            # Brand filter
            if filter_brand != "All" and tds.get("brand") != filter_brand:
                continue
            # Owner filter
            if filter_owner != "All" and tds.get("owner") != filter_owner:
                    continue
            # (Source filter removed)
            # Search filter
            if search:
                search_text = " ".join([
                    metadata.get("product_name", ""),
                    tds.get("brand", ""),
                    metadata.get("supplier_name", ""),
                    metadata.get("generic_product_name", "")
                ]).lower()
                if search.lower() not in search_text:
                    continue
            filtered.append(tds)

        # Display filter summary
        if filtered:
            st.success(f"📋 Found {len(filtered)} TDS records matching your filters")
        else:
            st.info("No TDS records match the current filters.")

        if not filtered:
            st.info("No TDS records match the current filters.")
        else:
            # Group by category then brand
            by_cat = {}
            for tds in filtered:
                metadata = tds.get("metadata", {})
                category = metadata.get("category", "Unknown")
                brand = tds.get("brand", "Unknown")
                by_cat.setdefault(category, {}).setdefault(brand, []).append(tds)

            for cat, brands in by_cat.items():
                with st.expander(f"📁 {cat}", expanded=False):
                    for brand, items in brands.items():
                        for tds in items:
                            tid = tds["id"]
                            metadata = tds.get("metadata", {})
                            cols = st.columns([3, 2, 2, 2])
                            with cols[0]:
                                _ptype = metadata.get('product_type', '') or 'N/A'
                                _brand = tds.get('brand', '') or 'N/A'
                                st.markdown(f"**{_ptype} — {_brand}**")
                                st.caption(f"Product: {metadata.get('product_name', 'Unknown Product')}")
                                st.caption(f"Generic: {metadata.get('generic_product_name', 'N/A')}")
                                st.caption(f"Supplier: {metadata.get('supplier_name', 'N/A')}")
                            with cols[1]:
                                st.write(f"Owner: {tds.get('owner', 'N/A')}")
                                st.write(f"Source: {tds.get('source', 'N/A')}")
                            with cols[2]:
                                tds_url = metadata.get("tds_file_url")
                                if tds_url:
                                    st.markdown(f"[📄 Download TDS]({tds_url})")
                                else:
                                    st.write("No TDS file")
                            with cols[3]:
                                if st.button("✏️ Edit", key=f"edit_{tid}"):
                                    st.session_state[f"editing_{tid}"] = True

                            if st.session_state.get(f"editing_{tid}"):
                                # Use a refresh token to force expander identity change and collapse after save/cancel
                                _tds_refresh_token = st.session_state.get("tds_manage_refresh_token", "")
                                try:
                                    _nzw_t = ((sum(ord(ch) for ch in _tds_refresh_token) % 5) + 1) if _tds_refresh_token else 0
                                except Exception:
                                    _nzw_t = 0
                                _zw_sfx_t = "\u200B" * _nzw_t if _nzw_t else ""
                                with st.expander(f"Edit: {metadata.get('product_name', 'Unknown Product')}{_zw_sfx_t}", expanded=False):
                                    # Editable fields for TDS data
                                    ename = st.text_input("Product Name", value=metadata.get("product_name", ""), key=f"n_{tid}")
                                    ecat = st.selectbox("Category", FIXED_CATEGORIES, index=FIXED_CATEGORIES.index(metadata.get("category", "Others")), key=f"c_{tid}")
                                    etype = st.text_input("Product Type", value=metadata.get("product_type", ""), key=f"t_{tid}")
                                    ebrand = st.text_input("Brand", value=tds.get("brand", ""), key=f"b_{tid}")
                                    egrade = st.text_input("Grade", value=tds.get("grade", ""), key=f"g_{tid}")
                                    eowner = st.selectbox("Owner", ["Supplier", "Customer", "Competitor"], index=["Supplier", "Customer", "Competitor"].index(tds.get("owner", "Supplier")), key=f"o_{tid}")
                                    esource = st.text_input("Source", value=tds.get("source", ""), key=f"s_{tid}")
                                    egenname = st.text_input("Generic Product Name", value=metadata.get("generic_product_name", ""), key=f"gn_{tid}")
                                    etradename = st.text_input("Trade Name", value=metadata.get("trade_name", ""), key=f"tn_{tid}")
                                    esupplier = st.text_input("Supplier Name", value=metadata.get("supplier_name", ""), key=f"sn_{tid}")
                                    epackaging = st.text_input("Packaging Size & Type", value=metadata.get("packaging_size_type", ""), key=f"p_{tid}")
                                    _specs_src = tds.get("specs") or {}
                                    _net_w_fallback = metadata.get("net_weight") or _specs_src.get("net_weight") or ""
                                    _tech_fallback = (
                                        metadata.get("technical_spec")
                                        or _specs_src.get("technical_specification")
                                        or _specs_src.get("technical_spec")
                                        or ""
                                    )
                                    enetweight = st.text_input("Net Weight", value=_net_w_fallback, key=f"nw_{tid}")
                                    etspec = st.text_area("Technical Specification", value=_tech_fallback, key=f"ts_{tid}")
                                    edesc = st.text_area("Description", value=metadata.get("description", ""), key=f"desc_{tid}")
                                    
                                    # LeanChems Product Status
                                    eleanchems = st.selectbox(
                                        "Is it Leanchems legacy/existing/coming product?",
                                        ["Yes", "No"],
                                        index=0 if metadata.get("is_leanchems_product") == "Yes" else 1,
                                        key=f"leanchems_{tid}"
                                    )
                                    
                                    # Supporting Documents section (upload, list, delete)
                                    st.markdown("---")
                                    st.subheader("📎 Supporting Documents")
                                    st.info("Upload any related files (e.g., brochures, test reports). Stored under this TDS record.")
                                    supporting_files = metadata.get("supporting_files", [])
                                    if supporting_files:
                                        st.write("**Current Supporting Files:**")
                                        sel_indices = st.multiselect(
                                            "Select files to delete",
                                            options=list(range(len(supporting_files))),
                                            format_func=lambda i: supporting_files[i].get('name', f'File {i+1}') if i is not None else "",
                                            key=f"supp_del_sel_{tid}"
                                        )
                                        for i, fobj in enumerate(supporting_files):
                                            col_s1, col_s2, col_s3 = st.columns([4,1,1])
                                            with col_s1:
                                                name = fobj.get('name', 'Unknown file')
                                                url = fobj.get('url')
                                                if url:
                                                    st.markdown(f"[📄 {name}]({url})")
                                                else:
                                                    st.write(f"📄 {name}")
                                            with col_s2:
                                                st.write(f"{(fobj.get('size') or 0) / 1024:.1f} KB")
                                            with col_s3:
                                                st.caption(fobj.get('type', '').upper())
                                        if st.button("🗑️ Delete selected", key=f"del_supp_{tid}"):
                                            try:
                                                remaining = []
                                                for i, f in enumerate(supporting_files):
                                                    if i in sel_indices:
                                                        _delete_storage_object_by_url(f.get('url') or '')
                                                    else:
                                                        remaining.append(f)
                                                updated_meta = metadata.copy()
                                                updated_meta["supporting_files"] = remaining
                                                supabase.table("tds_data").update({"metadata": updated_meta}).eq("id", tid).execute()
                                                st.success("Selected supporting files deleted")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Failed to delete files: {e}")
                                    
                                    new_supporting = st.file_uploader(
                                        "Upload Supporting Files",
                                        type=ALLOWED_FILE_EXTS, 
                                        accept_multiple_files=True,
                                        key=f"supp_up_{tid}"
                                    )

                                    # Actions
                                    ac1, ac2 = st.columns(2)
                                    with ac1:
                                        if st.button("💾 Save", key=f"save_{tid}"):
                                            # Validations
                                            n_ok, n_msg = validate_product_name(ename)
                                            if not n_ok:
                                                st.error(n_msg)
                                            elif name_exists_other(ename, tds.get("chemical_type_id") or ""):
                                                st.error("Another product already uses this name")
                                            else:
                                                # Build updates
                                                def _strip_or_empty(v: str | None) -> str:
                                                    try:
                                                        return (v or "").strip()
                                                    except Exception:
                                                        return ""
                                                def _strip_or_none(v: str | None):
                                                    s = _strip_or_empty(v)
                                                    return s if s else None
                                                updates = {
                                                    "name": _strip_or_empty(ename),
                                                    "category": ecat,
                                                    "description": _strip_or_none(edesc),
                                                    "is_leanchems_product": eleanchems,
                                                }

                                                # Upload supporting files
                                                if new_supporting:
                                                    supp_files = metadata.get("supporting_files", []).copy()
                                                    for uploaded_file in new_supporting:
                                                        okf, msgf = validate_file(uploaded_file)
                                                        if not okf:
                                                            st.error(f"File {uploaded_file.name}: {msgf}")
                                                            continue
                                                        try:
                                                            url, fname, fsize, ftype = upload_supporting_doc(uploaded_file, tid)
                                                            supp_files.append({
                                                                "url": url,
                                                                "name": fname,
                                                                "size": fsize,
                                                                "type": ftype,
                                                                "uploaded_at": datetime.utcnow().isoformat() + "Z"
                                                            })
                                                        except Exception as e:
                                                            st.error(f"Failed to upload {uploaded_file.name}: {e}")
                                                    updates["supporting_files"] = supp_files

                                                # Update TDS data
                                                try:
                                                    # Update metadata
                                                    updated_metadata = metadata.copy()
                                                    updated_metadata.update({
                                                        "product_name": _strip_or_empty(ename),
                                                        "category": ecat,
                                                        "product_type": _strip_or_empty(etype),
                                                        "generic_product_name": _strip_or_none(egenname),
                                                        "trade_name": _strip_or_none(etradename),
                                                        "supplier_name": _strip_or_none(esupplier),
                                                        "packaging_size_type": _strip_or_none(epackaging),
                                                        "net_weight": _strip_or_none(enetweight),
                                                        "technical_spec": _strip_or_none(etspec),
                                                        "description": _strip_or_none(edesc),
                                                        "is_leanchems_product": eleanchems,
                                                    })
                                                    # Bring through file-related updates into metadata for consistency
                                                    if "supporting_files" in updates:
                                                        updated_metadata["supporting_files"] = updates["supporting_files"]
                                                    for _k in ["tds_file_url","tds_file_name","tds_file_size","tds_file_type"]:
                                                        if _k in updates:
                                                            updated_metadata[_k] = updates[_k]
                                                    
                                                    # Update TDS record
                                                    tds_updates = {
                                                        "brand": _strip_or_none(ebrand),
                                                        "grade": _strip_or_none(egrade),
                                                        "owner": eowner,
                                                        "source": _strip_or_none(esource),
                                                        "metadata": updated_metadata
                                                    }
                                                    
                                                    supabase.table("tds_data").update(tds_updates).eq("id", tid).execute()
                                                    st.success("✅ TDS record updated")
                                                    st.session_state.pop(f"editing_{tid}", None)
                                                    # Bump token so the expander resets on rerun
                                                    st.session_state["tds_manage_refresh_token"] = str(uuid.uuid4())
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Failed to update: {e}")

                                    with ac2:
                                        if st.button("❌ Cancel", key=f"cancel_{tid}"):
                                            st.session_state.pop(f"editing_{tid}", None)
                                            st.session_state["tds_manage_refresh_token"] = str(uuid.uuid4())

    st.markdown('</div>', unsafe_allow_html=True)

# UI - View TDS
if st.session_state.get("main_section") == "sourcing" and st.session_state.get("sourcing_section") == "view" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">View TDS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # Filters (Category, Brand, Owner, Source, Search)
    st.subheader("📊 Filter TDS Records")
    colf1, colf2, colf3 = st.columns([2, 2, 2])
    with colf1:
        filter_category_v = st.selectbox("Filter by Category", ["All"] + FIXED_CATEGORIES, key="view_filter_category")
    with colf2:
        all_product_types_v = []
        try:
            _res_v = supabase.table("tds_data").select("metadata").execute()
            for row in (_res_v.data or []):
                metadata = row.get("metadata", {})
                product_type = metadata.get("product_type")
                if product_type:
                    all_product_types_v.append(product_type)
            all_product_types_v = sorted(list(set(all_product_types_v)))
        except Exception:
            pass
        filter_product_type_v = st.selectbox("Filter by Product Type", ["All"] + all_product_types_v, key="view_filter_product_type")
    with colf3:
        filter_owner_v = st.selectbox("Filter by Owner", ["All", "Supplier", "Customer", "Competitor"], key="view_filter_owner")

    search_view = st.text_input("Search by product name/brand/supplier", placeholder="Start typing...", key="view_filter_search")

    # Fetch TDS records and apply filters
    try:
        tds_records = supabase.table("tds_data").select("*").execute()
        all_tds = tds_records.data or []
    except Exception as e:
        st.error(f"Failed to fetch TDS records: {e}")
        all_tds = []

    filtered_tds = []
    for tds in all_tds:
        metadata = tds.get("metadata", {})
        if filter_category_v != "All" and metadata.get("category") != filter_category_v:
            continue
        if filter_product_type_v != "All" and metadata.get("product_type") != filter_product_type_v:
            continue
        if filter_owner_v != "All" and tds.get("owner") != filter_owner_v:
            continue
        # (Source filter removed)
        if search_view:
            search_text = " ".join([
                metadata.get("product_name", ""),
                tds.get("brand", ""),
                metadata.get("supplier_name", ""),
                metadata.get("generic_product_name", "")
            ]).lower()
            if search_view.lower() not in search_text:
                continue
        filtered_tds.append(tds)

    if not filtered_tds:
        st.info("📭 No TDS records found with current filters.")
        st.markdown("💡 Adjust filters or add new TDS records in the Add tab.")
    else:
        # Group by product type
        by_product_type = {}
        for tds in filtered_tds:
            metadata = tds.get("metadata", {})
            product_type = metadata.get("product_type", "Unknown")
            by_product_type.setdefault(product_type, []).append(tds)

        # Export button
        col_export1, col_export2 = st.columns([1, 3])
        with col_export1:
            if st.button("📊 Export CSV", type="secondary", key="export_csv_view_tds"):
                try:
                    import pandas as pd
                    # Prepare data for export
                    export_data = []
                    for tds in filtered_tds:
                        metadata = tds.get("metadata", {})
                        export_data.append({
                            "Product Name": metadata.get("product_name", ""),
                            "Generic Name": metadata.get("generic_product_name", ""),
                            "Trade Name": metadata.get("trade_name", ""),
                            "Brand": tds.get("brand", ""),
                            "Grade": tds.get("grade", ""),
                            "Supplier": metadata.get("supplier_name", ""),
                            "Owner": tds.get("owner", ""),
                            "Source": tds.get("source", ""),
                            "Category": metadata.get("category", ""),
                            "TDS File": metadata.get("tds_file_name", "No TDS"),
                            "Leanchems Product": metadata.get("is_leanchems_product", "No"),
                            "Created": tds.get("created_at", "")
                        })
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"tds_records_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")

        st.markdown(f"**Found {len(filtered_tds)} TDS records**")

        # Display TDS records grouped by product type
        for product_type, tds_list in by_product_type.items():
            with st.expander(f"🏷️ {product_type} ({len(tds_list)} records)", expanded=False):
                for tds in tds_list:
                    tid = tds["id"]
                    metadata = tds.get("metadata", {})
                    
                    # TDS record card
                    with st.container():
                        st.markdown("---")
                        
                        # Main info row
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            _ptype = metadata.get('product_type', '') or 'N/A'
                            _brand = tds.get('brand', '') or 'N/A'
                            st.markdown(f"**{_ptype} — {_brand}**")
                            st.caption(f"Product: {metadata.get('product_name', 'Unknown Product')}")
                            st.caption(f"Generic: {metadata.get('generic_product_name', 'N/A')}")
                            # Show LeanChems status
                            leanchems_status = metadata.get("is_leanchems_product", "No")
                            if leanchems_status == "Yes":
                                st.caption("🏢 Leanchems Product")
                        
                        with col2:
                            # TDS status and download
                            tds_url = metadata.get("tds_file_url")
                            if tds_url:
                                st.markdown("📄 **TDS:** Available")
                                st.markdown(f"[Download TDS]({tds_url})")
                                st.caption(f"File: {metadata.get('tds_file_name', 'Unknown')}")
                            else:
                                st.markdown("📄 **TDS:** Not available")
                        
                        with col3:
                            if st.button("👁️ View Details", key=f"view_{tid}"):
                                st.session_state[f"viewing_{tid}"] = True

                        # View Details Modal
                        if st.session_state.get(f"viewing_{tid}"):
                            with st.expander(f"📋 Full Details: {metadata.get('product_name', 'Unknown Product')}", expanded=False):
                                st.markdown("**Product Information**")
                                st.write(f"**Product Name:** {metadata.get('product_name', 'N/A')}")
                                st.write(f"**Generic Product Name:** {metadata.get('generic_product_name', 'N/A')}")
                                st.write(f"**Trade Name:** {metadata.get('trade_name', 'N/A')}")
                                st.write(f"**Category:** {metadata.get('category', 'N/A')}")
                                st.write(f"**Product Type:** {metadata.get('product_type', 'N/A')}")
                                
                                st.markdown("**Supplier Information**")
                                st.write(f"**Supplier Name:** {metadata.get('supplier_name', 'N/A')}")
                                st.write(f"**Brand:** {tds.get('brand', 'N/A')}")
                                st.write(f"**Grade:** {tds.get('grade', 'N/A')}")
                                st.write(f"**Owner:** {tds.get('owner', 'N/A')}")
                                st.write(f"**Source:** {tds.get('source', 'N/A')}")
                                
                                st.markdown("**Packaging & Specifications**")
                                _specs_src = tds.get("specs") or {}
                                _net_w = metadata.get('net_weight') or _specs_src.get('net_weight') or 'N/A'
                                st.write(f"**Packaging Size & Type:** {metadata.get('packaging_size_type', 'N/A')}")
                                st.write(f"**Net Weight:** {_net_w}")
                                
                                # Technical Specification (render as normal text to keep consistent font)
                                tech_spec = metadata.get("technical_spec") or _specs_src.get("technical_specification") or _specs_src.get("technical_spec")
                                if tech_spec:
                                    st.markdown("**Technical Specification:**")
                                    st.text(tech_spec)
                                
                                # TDS Information
                                st.markdown("**Technical Data Sheet**")
                                tds_url = metadata.get("tds_file_url")
                                if tds_url:
                                    col_tds1, col_tds2 = st.columns(2)
                                    with col_tds1:
                                        st.write(f"**TDS File:** {metadata.get('tds_file_name', 'Unknown')}")
                                        st.write(f"**Size:** {metadata.get('tds_file_size', 0) / 1024:.1f} KB")
                                    with col_tds2:
                                        st.write(f"**Type:** {metadata.get('tds_file_type', 'Unknown')}")
                                        st.markdown(f"[📥 Download TDS]({tds_url})")
                                else:
                                    st.write("No TDS file uploaded")
                                
                                # Close button
                                if st.button("❌ Close Details", key=f"close_{tid}"):
                                    st.session_state.pop(f"viewing_{tid}", None)

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - Chemical Master Data
# ==========================
if st.session_state.get("main_section") == "chemical" and has_chemical_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Chemical Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # Track current chemical tab to detect tab switches
    if "chemical_current_tab" not in st.session_state:
        st.session_state["chemical_current_tab"] = "Add Chemical"
    
    # Create custom tab navigation with proper change detection
    tab_col1, tab_col2, tab_col3 = st.columns(3)
    
    with tab_col1:
        if st.button("Add Chemical", key="chem_tab_add", type="primary" if st.session_state.get("chemical_current_tab") == "Add Chemical" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("chemical_current_tab")
            if previous_tab and previous_tab != "Add Chemical" and _has_unsaved_chemical_changes():
                st.session_state["pending_chemical_tab"] = "Add Chemical"
                st.rerun()
            else:
                st.session_state["chemical_current_tab"] = "Add Chemical"
                st.rerun()
    
    with tab_col2:
        if st.button("Manage Chemicals", key="chem_tab_manage", type="primary" if st.session_state.get("chemical_current_tab") == "Manage Chemicals" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("chemical_current_tab")
            if previous_tab and previous_tab != "Manage Chemicals" and _has_unsaved_chemical_changes():
                st.session_state["pending_chemical_tab"] = "Manage Chemicals"
                st.rerun()
            else:
                st.session_state["chemical_current_tab"] = "Manage Chemicals"
                st.rerun()
    
    with tab_col3:
        if st.button("View Chemicals", key="chem_tab_view", type="primary" if st.session_state.get("chemical_current_tab") == "View Chemicals" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("chemical_current_tab")
            if previous_tab and previous_tab != "View Chemicals" and _has_unsaved_chemical_changes():
                st.session_state["pending_chemical_tab"] = "View Chemicals"
                st.rerun()
            else:
                st.session_state["chemical_current_tab"] = "View Chemicals"
                st.rerun()
    
    # Handle pending tab changes with confirmation dialog
    if st.session_state.get("pending_chemical_tab"):
        new_tab = st.session_state.get("pending_chemical_tab")
        previous_tab = st.session_state.get("chemical_current_tab")
        
        if previous_tab == "Add Chemical":
            st.warning("⚠️ You have unsaved changes in the Add Chemical tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_chem_add", type="primary"):
                    _clear_chemical_editing_session()
                    st.session_state["chemical_current_tab"] = new_tab
                    st.session_state.pop("pending_chemical_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_chem_add"):
                    st.session_state.pop("pending_chemical_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif previous_tab == "Manage Chemicals":
            st.warning("⚠️ You have unsaved changes in the Manage Chemicals tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_chem_manage", type="primary"):
                    _clear_chemical_editing_session()
                    st.session_state["chemical_current_tab"] = new_tab
                    st.session_state.pop("pending_chemical_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_chem_manage"):
                    st.session_state.pop("pending_chemical_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
    
    # Get current tab for rendering
    current_tab = st.session_state.get("chemical_current_tab", "Add Chemical")

    # -------- Add Chemical --------
    if current_tab == "Add Chemical":
        st.subheader("Add Chemical")
        if gemini_model:
            st.caption("Type a chemical name and press Enter to analyze with AI and check duplicates.")
        else:
            st.caption("Type a chemical name and press Enter to check duplicates. AI analysis is not available.")

        # Mapping selects at the top (before Type Chemical Name)
        st.markdown("---")
        st.caption("Select Category and Product Type from mapping")
        _chem_cat_placeholder = "— Select —"
        _chem_cat_options = [_chem_cat_placeholder] + FIXED_CATEGORIES
        st.markdown("**Category**")
        _chem_cat_sel = st.selectbox(
            "Category",
            options=_chem_cat_options,
            key="chem_seg_select",
            label_visibility="collapsed"
        )
        selected_segment = "" if _chem_cat_sel == _chem_cat_placeholder else _chem_cat_sel
        add_new_seg = st.checkbox("Add new category", key="chem_add_new_seg")
        if add_new_seg:
            new_seg = st.text_input("New Category Name", key="chem_new_seg")
            if new_seg:
                selected_segment = new_seg.strip()

        # Persist selections for save logic (no direct widget key to avoid conflicts)
        st.session_state["chem_selected_category"] = selected_segment
        st.markdown(f"**Selected Category:** {selected_segment or '-'}")

        with st.form("chem_add_form", clear_on_submit=False):
            st.markdown("**Type Chemical Name**")
            chem_name_input = st.text_input("Type Chemical Name:", placeholder="e.g., Redispersible Polymer Powder", label_visibility="collapsed")
            if gemini_model:
                analyze_submit = st.form_submit_button("Analyze & Prefill")
            else:
                analyze_submit = st.form_submit_button("Check Duplicates")

        # Always get the latest extracted data from session state
        extracted = st.session_state.get("chem_ai_extracted", {})

        # Trigger analysis when Enter pressed (form submitted)
        if analyze_submit:
            # Duplicate suggestions
            duplicates = search_chemicals_by_name(chem_name_input)
            if duplicates:
                st.warning(f"Found {len(duplicates)} possible duplicates:")
                for d in duplicates[:5]:
                    dup_name = d.get("generic_name") or "(unnamed)"
                    dup_seg = ", ".join(d.get("industry_segments") or [])
                    dup_cat = ", ".join(d.get("functional_categories") or [])
                    st.write(f"• {dup_name} — {dup_seg} | {dup_cat}")

            # AI extraction
            if gemini_model:
                with st.spinner("Analyzing chemical with AI..."):
                    ai_data = analyze_chemical_with_ai(chem_name_input)
                    if ai_data:
                        st.session_state["chem_ai_extracted"] = ai_data
                        extracted = ai_data
                        st.success("AI extraction completed.")
                        st.rerun()  # Refresh the form to show prefilled data
                    else:
                        st.error("AI extraction failed or not configured.")
            else:
                st.info("AI analysis is not available. You can still manually fill in the fields below.")

        # Helpers
        def csv_default(val):
            return ", ".join(val) if isinstance(val, list) else (val or "")
        def parse_csv_list(text_val: str) -> list[str]:
            return [s.strip() for s in (text_val or "").split(",") if s.strip()]
        def parse_json_list(text_val: str):
            try:
                import json
                data = json.loads(text_val)
                return data if isinstance(data, list) else []
            except Exception:
                return []
        # Accept either a JSON array or one-JSON-object-per-line without brackets
        def parse_json_lines_or_array(text_val: str):
            try:
                import json as _json_p
                txt = (text_val or "").strip()
                if not txt:
                    return []
                # Try array first
                try:
                    arr = _json_p.loads(txt)
                    if isinstance(arr, list):
                        return arr
                    if isinstance(arr, dict):
                        return [arr]
                except Exception:
                    pass
                # Fallback: parse one JSON object per non-empty line
                items = []
                for line in txt.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = _json_p.loads(line)
                        if isinstance(obj, dict):
                            items.append(obj)
                    except Exception:
                        # ignore unparsable lines
                        continue
                return items
            except Exception:
                return []

        # Helper to show AI suggestion text under each control
        import json as _json_for_ai_view
        def _ai_view(value):
            if value is None:
                return ""
            if isinstance(value, (list, dict)):
                try:
                    return _json_for_ai_view.dumps(value, ensure_ascii=False)
                except Exception:
                    return str(value)
            return str(value)
        # Render list of objects as newline-delimited JSON objects (no square brackets)
        def _ai_list_as_lines(value):
            try:
                if isinstance(value, list):
                    # Render list of dicts as human-readable key: value pairs per line
                    rendered_lines = []
                    for item in value:
                        if isinstance(item, dict):
                            parts = []
                            for k, v in item.items():
                                if v is None:
                                    continue
                                parts.append(f"{k}: {v}")
                            rendered_lines.append(", ".join(parts) if parts else _json_for_ai_view.dumps(item, ensure_ascii=False)
                            )
                        else:
                            rendered_lines.append(str(item))
                    return "\n".join(rendered_lines)
                return _ai_view(value)
            except Exception:
                return _ai_view(value)

        # Parse relaxed human-readable "key: value, key: value" lines into list of dicts
        def _parse_kv_lines(text_val: str):
            items = []
            try:
                txt = (text_val or "").strip()
                if not txt:
                    return []
                for line in txt.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    entry = {}
                    for pair in [p for p in line.split(",") if p.strip()]:
                        if ":" in pair:
                            k, v = pair.split(":", 1)
                            k = k.strip()
                            v = v.strip()
                            if k:
                                entry[k] = v
                    if entry:
                        items.append(entry)
                return items
            except Exception:
                return items

        # Prefilled editable fields (reordered to requested sequence)
        # 1) Summary 80/20
        st.markdown("**Summary 80/20 (5–7 bullets)**")
        chem_sum_8020 = st.text_area("Summary 80/20 (5–7 bullets)", value=extracted.get("summary_80_20", ""), height=80, label_visibility="collapsed")
        # 2) Synonyms
        st.markdown("**Synonyms (comma-separated)**")
        chem_syn = st.text_input("Synonyms (comma-separated)", value=csv_default(extracted.get("synonyms", [])), label_visibility="collapsed")
        # 3) Family
        st.markdown("**Family**")
        chem_family = st.text_input("Family", value=extracted.get("family", ""), label_visibility="collapsed")
        # 4) Generic Name
        st.markdown("**Generic Name**")
        chem_gen = st.text_input("Generic Name", value=extracted.get("generic_name", ""), label_visibility="collapsed")
        # 5) HS Codes (code only)
        def _hs_codes_as_csv():
            try:
                items = extracted.get("hs_codes") if extracted else []
                codes = []
                for it in items or []:
                    if isinstance(it, dict) and it.get("code"):
                        codes.append(str(it.get("code")))
                return ", ".join(codes)
            except Exception:
                return ""
        st.markdown("**HS Codes**")
        chem_hs_codes = st.text_input("HS Codes", value=_hs_codes_as_csv(), label_visibility="collapsed")
        # 6) CAS IDs
        st.markdown("**CAS IDs**")
        chem_cas = st.text_input("CAS IDs", value=csv_default(extracted.get("cas_ids", [])), label_visibility="collapsed")
        # 7) Summary Technical
        st.markdown("**Summary Technical**")
        chem_sum_tech = st.text_area("Summary Technical", value=extracted.get("summary_technical", ""), height=100, label_visibility="collapsed")
        # 8) Functional Categories
        st.markdown("**Functional Categories**")
        chem_func = st.text_input("Functional Categories", value=csv_default(extracted.get("functional_categories", [])), label_visibility="collapsed")
        # 9) Industry Segments
        st.markdown("**Industry Segments**")
        chem_inds = st.text_input("Industry Segments", value=csv_default(extracted.get("industry_segments", [])), label_visibility="collapsed")
        # 10) Key Applications
        st.markdown("**Key Applications**")
        chem_keys = st.text_input("Key Applications", value=csv_default(extracted.get("key_applications", [])), label_visibility="collapsed")
        # 11) Typical Dosage
        st.markdown("**Typical Dosage**")
        chem_dosage_json = st.text_area("Typical Dosage", value=_ai_list_as_lines(extracted.get("typical_dosage")) if extracted else "", height=80, label_visibility="collapsed")
        # 12) Physical Snapshot
        st.markdown("**Physical Snapshot**")
        chem_phys_json = st.text_area("Physical Snapshot", value=_ai_list_as_lines(extracted.get("physical_snapshot")) if extracted else "", height=80, label_visibility="collapsed")
        # 13) Compatibilities
        st.markdown("**Compatibilities**")
        chem_compat = st.text_input("Compatibilities", value=csv_default(extracted.get("compatibilities", [])), label_visibility="collapsed")
        # 14) Incompatibilities
        st.markdown("**Incompatibilities**")
        chem_incompat = st.text_input("Incompatibilities", value=csv_default(extracted.get("incompatibilities", [])), label_visibility="collapsed")
        # 15) Sensitivities
        st.markdown("**Sensitivities**")
        chem_sens = st.text_input("Sensitivities", value=csv_default(extracted.get("sensitivities", [])), label_visibility="collapsed")
        # 16) Appearance
        st.markdown("**Appearance**")
        chem_appearance = st.text_input("Appearance", value=extracted.get("appearance", ""), label_visibility="collapsed")
        # 17) Storage Conditions
        st.markdown("**Storage Conditions**")
        chem_storage = st.text_input("Storage Conditions", value=extracted.get("storage_conditions", ""), label_visibility="collapsed")
        # 18) Packaging Options
        st.markdown("**Packaging Options**")
        chem_pack = st.text_input("Packaging Options", value=csv_default(extracted.get("packaging_options", [])), label_visibility="collapsed")
        # 19) Shelf Life (months)
        st.markdown("**Shelf Life (months)**")
        chem_shelf = st.number_input("Shelf Life (months)", min_value=0, max_value=120, value=int(extracted.get("shelf_life_months", 0) if extracted else 0), step=1, label_visibility="collapsed")
        # 20) Data Completeness
        st.markdown("**Data Completeness**")
        chem_dc = st.slider("Data Completeness", min_value=0.0, max_value=1.0, value=float(extracted.get("data_completeness", 0.0) if extracted else 0.0), step=0.05, label_visibility="collapsed")

        # Show one-line source indicator
        if extracted:
            src = st.session_state.get("chem_ai_source")
            if src:
                st.caption(f"Source: {src}")

        if st.button("Save Chemical", type="primary"):
            # Basic validations
            base_name = normalize_chemical_name(chem_gen)
            if not base_name:
                st.error("Chemical name is required")
            elif chemical_name_exists(base_name):
                st.error("A chemical with this name already exists")
            else:
                try:
                    ai = st.session_state.get("chem_ai_extracted", {}) or {}
                    # Helper to choose manual value else AI
                    def prefer_manual_str(manual: str, ai_key: str):
                        v = (manual or "").strip()
                        if v:
                            return v
                        return (ai.get(ai_key) or "").strip() or None
                    def prefer_manual_csv(manual: str, ai_key: str):
                        lst = parse_csv_list(manual)
                        if lst:
                            return lst
                        return ai.get(ai_key) or []
                    def prefer_manual_jsonarr(manual: str, ai_key: str):
                        arr = parse_json_lines_or_array(manual)
                        if arr:
                            return arr
                        return ai.get(ai_key) or []

                    payload = {
                        "id": str(uuid.uuid4()),
                        "generic_name": base_name or ai.get("generic_name"),
                        "family": prefer_manual_str(chem_family, "family"),
                        "synonyms": prefer_manual_csv(chem_syn, "synonyms"),
                        "cas_ids": prefer_manual_csv(chem_cas, "cas_ids"),
                        "hs_codes": (
                            [
                                {"region": "WCO", "code": code}
                                for code in parse_csv_list(chem_hs_codes)
                            ]
                            or ai.get("hs_codes")
                            or []
                        ),
                        "functional_categories": prefer_manual_csv(chem_func, "functional_categories"),
                        "industry_segments": prefer_manual_csv(chem_inds, "industry_segments"),
                        "key_applications": prefer_manual_csv(chem_keys, "key_applications"),
                        "typical_dosage": (
                            _parse_kv_lines(chem_dosage_json)
                            or prefer_manual_jsonarr(chem_dosage_json, "typical_dosage")
                        ),
                        "appearance": prefer_manual_str(chem_appearance, "appearance"),
                        "physical_snapshot": (
                            _parse_kv_lines(chem_phys_json)
                            or prefer_manual_jsonarr(chem_phys_json, "physical_snapshot")
                        ),
                        "compatibilities": prefer_manual_csv(chem_compat, "compatibilities"),
                        "incompatibilities": prefer_manual_csv(chem_incompat, "incompatibilities"),
                        "sensitivities": prefer_manual_csv(chem_sens, "sensitivities"),
                        "shelf_life_months": int(chem_shelf or ai.get("shelf_life_months") or 0),
                        "storage_conditions": prefer_manual_str(chem_storage, "storage_conditions"),
                        "packaging_options": prefer_manual_csv(chem_pack, "packaging_options"),
                        "summary_80_20": prefer_manual_str(chem_sum_8020, "summary_80_20"),
                        "summary_technical": prefer_manual_str(chem_sum_tech, "summary_technical"),
                        "data_completeness": float(chem_dc or ai.get("data_completeness") or 0.0),
                    }
                    create_chemical(payload)
                    st.success("✅ Chemical saved successfully")
                    # Clear AI/session state and refresh Add form
                    try:
                        for k in [
                            "chem_ai_extracted",
                            "chem_ai_source",
                            "chem_ai_last_raw",
                        ]:
                            st.session_state.pop(k, None)
                    except Exception:
                        pass
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to save chemical: {e}")
        
        # Add clear session button if there are unsaved changes

    # -------- Manage Chemicals --------
    elif current_tab == "Manage Chemicals":
        st.subheader("Manage Chemicals")
        # Auth gate similar to Manage Products
        if not sb_user:
            st.info("Please sign in to access Manage Chemicals.")
        elif not is_manager:
            st.error("You do not have permission to access Manage Chemicals.")
        else:
            # Filters
            colmf1, colmf2 = st.columns(2)
            with colmf1:
                seg_filter = st.text_input("Filter by Industry Segment", placeholder="e.g., Dry-mix")
            with colmf2:
                cat_filter = st.text_input("Filter by Functional Category", placeholder="e.g., Polymer")
            search_chem = st.text_input("Search by generic name, synonym or application", placeholder="Start typing...")
            if st.button("Reset Filters", type="secondary"):
                seg_filter = ""
                cat_filter = ""
                search_chem = ""

            chems = fetch_chemicals()
            filtered_chems = []
            # If no filters provided, show everything by default
            if not seg_filter and not cat_filter and not search_chem:
                filtered_chems = chems
            else:
                filtered_chems = []
            for c in chems:
                # Normalize fields for matching
                seg_text = ", ".join(c.get("industry_segments") or []).lower()
                cat_text = ", ".join(c.get("functional_categories") or []).lower()
                gen_text = (c.get("generic_name") or "").lower()
                syn_text = ", ".join(c.get("synonyms") or []).lower()
                app_text = ", ".join(c.get("key_applications") or []).lower()

                if seg_filter and seg_filter.lower() not in seg_text:
                    continue
                if cat_filter and cat_filter.lower() not in cat_text:
                    continue
                if search_chem:
                    q = search_chem.lower()
                    if all(q not in field for field in [gen_text, syn_text, cat_text, seg_text, app_text]):
                        continue
                if seg_filter or cat_filter or search_chem:
                    filtered_chems.append(c)

            if filtered_chems:
                st.success(f"📋 Found {len(filtered_chems)} chemicals")
            else:
                # Fallback: show all chemicals so user can edit/delete
                if chems:
                    st.warning("No chemicals match the filters. Showing all chemicals.")
                    filtered_chems = chems
                else:
                    st.info("No chemicals found in the database.")

            for chem in filtered_chems:
                cid = chem.get("id")
                # Expander reset suffix to force collapse after save via refresh token
                _chem_refresh_token = st.session_state.get("chem_manage_refresh_token", "")
                try:
                    _nzw = ((sum(ord(ch) for ch in _chem_refresh_token) % 5) + 1) if _chem_refresh_token else 0
                except Exception:
                    _nzw = 0
                _zw_suffix = "\u200B" * _nzw if _nzw else ""
                with st.expander(f"🧪 {chem.get('generic_name')}{_zw_suffix}", expanded=False):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        ename = st.text_input("Generic Name", value=chem.get("generic_name", ""), key=f"cn_{cid}")
                        efamily = st.text_input("Family", value=chem.get("family", ""), key=f"cf_{cid}")
                        esyn = st.text_input("Synonyms (comma-separated)", value=", ".join(chem.get("synonyms") or []), key=f"csy_{cid}")
                        ecas = st.text_input("CAS IDs (comma-separated)", value=", ".join(chem.get("cas_ids") or []), key=f"cca_{cid}")
                    with ec2:
                        # Human-readable HS Codes (comma-separated)
                        _hs_list = []
                        try:
                            for it in (chem.get("hs_codes") or []):
                                if isinstance(it, dict) and it.get("code"):
                                    _hs_list.append(str(it.get("code")))
                        except Exception:
                            pass
                        if not _hs_list and chem.get("hs_code"):
                            _hs_list = [str(chem.get("hs_code"))]
                        ehs_text = st.text_input("HS Codes (comma-separated)", value=", ".join(_hs_list), key=f"ch_{cid}")
                        efunc = st.text_input("Functional Categories (comma-separated)", value=", ".join(chem.get("functional_categories") or []), key=f"cc_{cid}")
                        eind = st.text_input("Industry Segments (comma-separated)", value=", ".join(chem.get("industry_segments") or []), key=f"ci_{cid}")
                    ekeys = st.text_input("Key Applications (comma-separated)", value=", ".join(chem.get("key_applications") or []), key=f"cak_{cid}")
                    # Human-readable Typical Dosage: one per line as "application: range"
                    edosage_lines = st.text_area("Typical Dosage (one per line: application: range)", value=_ai_list_as_lines(chem.get("typical_dosage")) if chem.get("typical_dosage") else "", height=70, key=f"cdj_{cid}")
                    eappearance = st.text_input("Appearance", value=chem.get("appearance", ""), key=f"cap_{cid}")
                    # Human-readable Physical Snapshot: one per line as "key: value, unit: U, method: M"
                    ephys_lines = st.text_area("Physical Snapshot (one per line: name: value, unit: U, method: M)", value=_ai_list_as_lines(chem.get("physical_snapshot")) if chem.get("physical_snapshot") else "", height=70, key=f"cps_{cid}")
                    ecompat = st.text_input("Compatibilities (comma-separated)", value=", ".join(chem.get("compatibilities") or []), key=f"ccom_{cid}")
                    eincompat = st.text_input("Incompatibilities (comma-separated)", value=", ".join(chem.get("incompatibilities") or []), key=f"cinc_{cid}")
                    esens = st.text_input("Sensitivities (comma-separated)", value=", ".join(chem.get("sensitivities") or []), key=f"csen_{cid}")
                    cs1, cs2 = st.columns(2)
                    with cs1:
                        eshelf = st.number_input("Shelf Life (months)", min_value=0, max_value=120, value=int(chem.get("shelf_life_months") or 0), step=1, key=f"csh_{cid}")
                        estorage = st.text_input("Storage Conditions", value=chem.get("storage_conditions", ""), key=f"cst_{cid}")
                    with cs2:
                        epack = st.text_input("Packaging Options (comma-separated)", value=", ".join(chem.get("packaging_options") or []), key=f"cpa_{cid}")
                        edc = st.slider("Data Completeness", 0.0, 1.0, float(chem.get("data_completeness") or 0.0), 0.05, key=f"cdc_{cid}")
                    e8020 = st.text_area("Summary 80/20", value=chem.get("summary_80_20", ""), height=60, key=f"c80_{cid}")
                    esumtech = st.text_area("Summary Technical", value=chem.get("summary_technical", ""), height=80, key=f"cstt_{cid}")

                    colb1, colb2, colb3 = st.columns([1,1,6])
                    with colb1:
                        if st.button("💾 Save", key=f"csave_{cid}"):
                            if not ename.strip():
                                st.error("Generic name cannot be empty")
                            elif chemical_name_exists(ename) and ename.strip() != (chem.get("generic_name") or ""):
                                # Re-use product helper for duplicate logic semantics
                                st.error("Another record already uses this name")
                            else:
                                try:
                                    updates = {
                                        "generic_name": ename.strip(),
                                        "family": efamily.strip() or None,
                                        "synonyms": [s.strip() for s in esyn.split(",") if s.strip()],
                                        "cas_ids": [s.strip() for s in ecas.split(",") if s.strip()],
                                        "hs_codes": (
                                            [
                                                {"region": "WCO", "code": code}
                                                for code in [s.strip() for s in ehs_text.split(",") if s.strip()]
                                            ]
                                        ),
                                        "functional_categories": [s.strip() for s in efunc.split(",") if s.strip()],
                                        "industry_segments": [s.strip() for s in eind.split(",") if s.strip()],
                                        "key_applications": [s.strip() for s in ekeys.split(",") if s.strip()],
                                        "typical_dosage": _parse_kv_lines(edosage_lines),
                                        "appearance": eappearance.strip() or None,
                                        "physical_snapshot": _parse_kv_lines(ephys_lines),
                                        "compatibilities": [s.strip() for s in ecompat.split(",") if s.strip()],
                                        "incompatibilities": [s.strip() for s in eincompat.split(",") if s.strip()],
                                        "sensitivities": [s.strip() for s in esens.split(",") if s.strip()],
                                        "shelf_life_months": int(eshelf or 0),
                                        "storage_conditions": estorage.strip() or None,
                                        "packaging_options": [s.strip() for s in epack.split(",") if s.strip()],
                                        "summary_80_20": e8020.strip() or None,
                                        "summary_technical": esumtech.strip() or None,
                                        "data_completeness": float(edc or 0.0),
                                    }
                                    update_chemical(cid, updates)
                                    st.success("✅ Updated")
                                    # Bump token so the expander identity changes and collapses on rerun
                                    st.session_state["chem_manage_refresh_token"] = str(uuid.uuid4())
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update: {e}")
                    with colb2:
                        if st.button("🗑️ Delete", key=f"cdel_{cid}"):
                            try:
                                delete_chemical(cid)
                                st.success("Deleted")
                                st.session_state["chem_manage_refresh_token"] = str(uuid.uuid4())
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")

    # -------- View Chemicals --------
    elif current_tab == "View Chemicals":
        st.subheader("View Chemicals")
        vcol1, vcol2 = st.columns(2)
        with vcol1:
            v_seg = st.text_input("Filter by Industry Segment")
        with vcol2:
            v_cat = st.text_input("Filter by Functional Category")
        v_search = st.text_input("Search by generic name or applications")

        chems = fetch_chemicals()
        v_filtered = []
        for c in chems:
            if v_seg and (", ".join(c.get("industry_segments") or [])).lower().find(v_seg.lower()) < 0:
                continue
            if v_cat and (", ".join(c.get("functional_categories") or [])).lower().find(v_cat.lower()) < 0:
                continue
            if v_search:
                hay = " ".join([
                    c.get("generic_name", ""),
                    ", ".join(c.get("industry_segments") or []),
                    ", ".join(c.get("functional_categories") or []),
                    ", ".join(c.get("key_applications") or []),
                ]).lower()
                if v_search.lower() not in hay:
                    continue
            v_filtered.append(c)

        # Compact table view from mapping
        if v_filtered:
            try:
                import pandas as _pd_view
            except Exception:
                _pd_view = None
            rows = _build_chem_view_rows(v_filtered, CHEM_VIEW_TABLE_FIELDS)
            if rows:
                try:
                    import pandas as pd
                    dfv = pd.DataFrame(rows)
                    st.dataframe(dfv, use_container_width=True, hide_index=True)
                except Exception:
                    # Fallback simple list rendering
                    for r in rows:
                        st.write(r)

        # Export CSV
        if st.button("📊 Export CSV", type="secondary", key="export_csv_view_chemicals"):
            try:
                import pandas as pd
                rows_csv = _build_chem_view_rows(v_filtered, CHEM_VIEW_TABLE_FIELDS)
                df = pd.DataFrame(rows_csv)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv,
                    file_name=f"chemicals_{datetime.utcnow().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

        if not v_filtered:
            st.info("No chemicals found with current filters.")
        else:
            for c in v_filtered:
                title_suffix = ", ".join(c.get('industry_segments') or [])
                with st.expander(f"🧪 {c.get('generic_name')} — {title_suffix}"):
                    for key, label in CHEM_VIEW_DETAIL_FIELDS:
                        st.markdown(f"**{label}:** {_format_chem_field(c.get(key))}")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - LeanChem Product Master Data (placeholder)
# ==========================
if st.session_state.get("main_section") == "leanchem":
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">LeanChem Product Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.info("🚧 Coming soon")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - Market Master Data (placeholder)
# ==========================
if st.session_state.get("main_section") == "market":
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Market Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.info("🚧 Coming soon")
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - Sourcing Master Data (coming soon)
# ==========================
if st.session_state.get("main_section") == "partner_master" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Partner Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.caption("Business partner")

    # If requested, programmatically switch to Manage tab after a save
    if st.session_state.get("partner_go_manage"):
        st.session_state.pop("partner_go_manage", None)
        st.markdown(
            """
            <script>
            setTimeout(function(){
              const tabs = Array.from(document.querySelectorAll('button[role="tab"]'));
              const manage = tabs.find(el => el.innerText && el.innerText.trim().toLowerCase().includes('manage'));
              if (manage) { manage.click(); }
            }, 50);
            </script>
            """,
            unsafe_allow_html=True,
        )

    # Create custom tab navigation with proper change detection
    tab_col1, tab_col2, tab_col3, tab_col4 = st.columns(4)
    
    with tab_col1:
        if st.button("Add Partner", key="partner_tab_add", type="primary" if st.session_state.get("partner_current_tab") == "Add Partner" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("partner_current_tab")
            if previous_tab and previous_tab != "Add Partner" and _has_unsaved_partner_changes():
                st.session_state["pending_partner_tab"] = "Add Partner"
                st.rerun()
            else:
                st.session_state["partner_current_tab"] = "Add Partner"
                st.rerun()
    
    with tab_col2:
        if st.button("Add Chemical", key="partner_tab_chem", type="primary" if st.session_state.get("partner_current_tab") == "Add Chemical" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("partner_current_tab")
            if previous_tab and previous_tab != "Add Chemical" and _has_unsaved_partner_changes():
                st.session_state["pending_partner_tab"] = "Add Chemical"
                st.rerun()
            else:
                st.session_state["partner_current_tab"] = "Add Chemical"
                st.rerun()
    
    with tab_col3:
        if st.button("Manage", key="partner_tab_manage", type="primary" if st.session_state.get("partner_current_tab") == "Manage" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("partner_current_tab")
            if previous_tab and previous_tab != "Manage" and _has_unsaved_partner_changes():
                st.session_state["pending_partner_tab"] = "Manage"
                st.rerun()
            else:
                st.session_state["partner_current_tab"] = "Manage"
                st.rerun()
    
    with tab_col4:
        if st.button("View", key="partner_tab_view", type="primary" if st.session_state.get("partner_current_tab") == "View" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("partner_current_tab")
            if previous_tab and previous_tab != "View" and _has_unsaved_partner_changes():
                st.session_state["pending_partner_tab"] = "View"
                st.rerun()
            else:
                st.session_state["partner_current_tab"] = "View"
                st.rerun()
    
    # Handle pending partner tab changes with confirmation dialog
    if st.session_state.get("pending_partner_tab"):
        new_tab = st.session_state.get("pending_partner_tab")
        previous_tab = st.session_state.get("partner_current_tab")
        
        if previous_tab == "Add Partner":
            st.warning("⚠️ You have unsaved changes in the Add Partner tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_partner_add", type="primary"):
                    _clear_partner_session()
                    st.session_state["partner_current_tab"] = new_tab
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_partner_add"):
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif previous_tab == "Add Chemical":
            st.warning("⚠️ You have unsaved changes in the Add Chemical tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_partner_chem", type="primary"):
                    _clear_partner_session()
                    st.session_state["partner_current_tab"] = new_tab
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_partner_chem"):
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif previous_tab == "Manage":
            st.warning("⚠️ You have unsaved changes in the Manage tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_partner_manage", type="primary"):
                    _clear_partner_session()
                    st.session_state["partner_current_tab"] = new_tab
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_partner_manage"):
                    st.session_state.pop("pending_partner_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
    
    # Get current tab for rendering
    current_partner_tab = st.session_state.get("partner_current_tab", "Add Partner")

    # Helpers for partner_data
    def fetch_partners():
        try:
            res = supabase.table("partner_data").select("*").order("partner").execute()
            return res.data or []
        except Exception as e:
            st.error(f"Failed to fetch partners: {e}")
            return []

    def _normalize_partner_name(name: str) -> str:
        try:
            return (name or "").strip().lower()
        except Exception:
            return name or ""

    def _fuzzy_match_partners(partner: str, country: str | None = None, threshold: float = 0.8) -> list[dict]:
        """Find similar partners using fuzzy matching"""
        try:
            from difflib import SequenceMatcher
            
            pname = _normalize_partner_name(partner)
            if not pname:
                return []
            
            rows = supabase.table("partner_data").select("id,partner,partner_country").execute().data or []
            similar_partners = []
            
            for r in rows:
                rn = _normalize_partner_name(r.get("partner") or "")
                rc = (r.get("partner_country") or "").strip().lower()
                country_match = country is None or rc == (country or "").strip().lower()
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, pname, rn).ratio()
                
                if similarity >= threshold and country_match:
                    similar_partners.append({
                        "id": r.get("id"),
                        "partner": r.get("partner"),
                        "partner_country": r.get("partner_country"),
                        "similarity": similarity
                    })
            
            # Sort by similarity score (highest first)
            return sorted(similar_partners, key=lambda x: x["similarity"], reverse=True)
        except Exception:
            return []

    def partner_exists(partner: str, country: str | None = None) -> bool:
        """Return True if a partner with same name (case-insensitive) and optional country exists."""
        try:
            pname = _normalize_partner_name(partner)
            if not pname:
                return False
            rows = supabase.table("partner_data").select("id,partner,partner_country").execute().data or []
            for r in rows:
                rn = _normalize_partner_name(r.get("partner") or "")
                if rn != pname:
                    continue
                if country is None:
                    return True
                rc = (r.get("partner_country") or "").strip().lower()
                if rc == (country or "").strip().lower():
                    return True
            return False
        except Exception:
            return False

    def create_partner(partner: str, country: str, selected_products: list[dict]):
        try:
            # Prevent duplicate partner by name+country
            if partner_exists(partner, country):
                st.error("Partner already exists with the same name and country")
                return None
            payload = {
                # id generated by DB default
                "partner": (partner or "").strip(),
                "partner_country": (country or "").strip(),
                # is_active defaults to true in DB
            }
            return supabase.table("partner_data").insert(payload).execute()
        except Exception as e:
            st.error(f"Failed to create partner: {e}")
            return None

    def update_partner(pid: str, updates: dict):
        try:
            updates_with_ts = {**updates, "updated_at": datetime.utcnow().isoformat() + "Z"}
            return supabase.table("partner_data").update(updates_with_ts).eq("id", pid).execute()
        except Exception as e:
            st.error(f"Failed to update partner: {e}")
            return None

    def delete_partner(pid: str):
        try:
            return supabase.table("partner_data").delete().eq("id", pid).execute()
        except Exception as e:
            st.error(f"Failed to delete partner: {e}")
            return None

    def list_all_tds():
        """Return list of products (name/category) that have a TDS uploaded, including file name/url."""
        try:
            res = supabase.table("tds_data").select("id,chemical_type_id,brand,grade,metadata").order("created_at", desc=True).execute()
            rows = res.data or []
            items = []
            for r in rows:
                meta = r.get("metadata") or {}
                # Only include when a TDS file URL exists
                if not meta.get("tds_file_url"):
                    continue
                items.append({
                    "id": r.get("id"),  # tds record id (for unique widget keys)
                    "chemical_type_id": r.get("chemical_type_id"),
                    "name": meta.get("product_name") or meta.get("generic_product_name") or (r.get("brand") or "Unnamed"),
                    "category": meta.get("category") or "Others",
                    "brand": r.get("brand"),
                    "tds_file_url": meta.get("tds_file_url"),
                    "tds_file_name": meta.get("tds_file_name"),
                })
            # Sort by category then name for stable UI
            items.sort(key=lambda x: (x.get("category") or "", x.get("name") or ""))
            return items
        except Exception as e:
            st.error(f"Failed to fetch list: {e}")
            return []

    def _ensure_chemical_type(name: str, category: str) -> str | None:
        """Find or create a chemical_types row by name and category; return id."""
        try:
            nm = (name or "").strip()
            cat = (category or "").strip() or "Others"
            if not nm:
                return None
            # Try find existing
            res = supabase.table("chemical_types").select("id").eq("name", nm).eq("category", cat).limit(1).execute()
            rows = res.data or []
            if rows:
                return rows[0].get("id")
            # Create minimal record
            payload = {"name": nm, "category": cat, "metadata": {}}
            ins = supabase.table("chemical_types").insert(payload).execute()
            # Fetch id from insert result
            newid = None
            try:
                newid = ((ins.data or [{}])[0] or {}).get("id")
            except Exception:
                newid = None
            if not newid:
                # Last resort: re-query
                res2 = supabase.table("chemical_types").select("id").eq("name", nm).eq("category", cat).limit(1).execute()
                rows2 = res2.data or []
                if rows2:
                    newid = rows2[0].get("id")
            return newid
        except Exception:
            return None

    def partner_get_products(partner_row: dict) -> list[dict]:
        """Return assigned products from metadata.tds_products field.
        Since tds_products and products columns don't exist, we only check metadata.tds_products.
        """
        try:
            md = partner_row.get("metadata") or {}
            if isinstance(md.get("tds_products"), list):
                result = md.get("tds_products") or []
                if result:
                    return result
        except Exception:
            pass
        return []

    def partner_set_products(partner_id: str, products: list[dict]) -> None:
        """Persist assigned products into metadata field.
        Since tds_products and products columns don't exist, we use metadata.tds_products.
        """
        try:
            curr = supabase.table("partner_data").select("metadata").eq("id", partner_id).limit(1).execute()
            curr_meta = ((curr.data or [{}])[0] or {}).get("metadata") or {}
            curr_meta["tds_products"] = products
            supabase.table("partner_data").update({"metadata": curr_meta}).eq("id", partner_id).execute()
        except Exception as e:
            st.error(f"Failed to update partner products: {e}")
            pass

    def _reset_session_keys(keys: list[str]):
        try:
            for k in keys:
                try:
                    st.session_state.pop(k, None)
                except Exception:
                    pass
        except Exception:
            pass

    def _reset_session_by_prefix(prefixes: list[str]):
        try:
            for k in list(st.session_state.keys()):
                if any(k.startswith(pfx) for pfx in prefixes):
                    try:
                        st.session_state.pop(k, None)
                    except Exception:
                        pass
        except Exception:
            pass

    if current_partner_tab == "Add Partner":
        st.subheader("Add Partner")
        partner_name = st.text_input("Partner Name *")
        # Country dropdown (ISO list)
        partner_country = st.selectbox("Partner Country *", COUNTRIES)
        # Add Partner is now only for creating the partner record
        st.markdown("---")
        st.caption("Fill in partner info and save. Assign chemicals in the 'Add Chemical' tab.")

        # Check for similar partners as user types
        if partner_name and partner_country:
            similar_partners = _fuzzy_match_partners(partner_name, partner_country, threshold=0.7)
            if similar_partners:
                st.warning("⚠️ Similar partners found:")
                for similar in similar_partners[:3]:  # Show top 3 matches
                    similarity_percent = int(similar["similarity"] * 100)
                    st.write(f"• {similar['partner']} ({similar['partner_country']}) - {similarity_percent}% similar")
                st.caption("Please review the list above to avoid creating duplicate partners.")

        if st.button("Save Partner", type="primary"):
            if not (partner_name and partner_country):
                st.error("Partner name and country are required")
            elif partner_exists(partner_name, partner_country):
                st.error("Partner already exists with the same name and country")
            else:
                # Check for very similar partners (high threshold) and block if found
                very_similar = _fuzzy_match_partners(partner_name, partner_country, threshold=0.9)
                if very_similar:
                    st.error("❌ Cannot create partner: Very similar partner already exists!")
                    st.write("**Similar partners found:**")
                    for similar in very_similar:
                        similarity_percent = int(similar["similarity"] * 100)
                        st.write(f"• {similar['partner']} ({similar['partner_country']}) - {similarity_percent}% similar")
                    st.caption("Please use a different name or check if this is the same partner.")
                else:
                    resp = create_partner(partner_name, partner_country, [])
                    if resp is not None:
                        st.success("✅ Partner saved")
                        # Reset Add Partner inputs
                        _reset_session_by_prefix(["pn_","pc_"]) 
                        st.rerun()
        
        # Add clear session button if there are unsaved changes

    elif current_partner_tab == "Add Chemical":
        st.subheader("Add Chemical to Partner")
        partners = fetch_partners()
        if not partners:
            st.info("No partners found. Please add a partner first in 'Add Partner'.")
        else:
            partner_labels = {f"{p.get('partner')} ({p.get('partner_country')})": p for p in partners}
            sel_label = st.selectbox("Select Partner", list(partner_labels.keys()))
            partner_obj = partner_labels.get(sel_label)
            tds_records = list_all_tds()
            if not tds_records:
                st.info("No TDS-backed chemicals found. Upload TDS in the TDS Master Data module.")
            else:
                # Get already assigned chemicals for this partner
                existing = partner_get_products(partner_obj)
                already_ids = {item.get('tds_id') for item in existing if isinstance(item, dict)}
                
                # Build label → id map only for unassigned chemicals
                options_map = {}
                for r in tds_records:
                    # Skip if already assigned to this partner
                    if r.get('id') in already_ids:
                        continue
                    
                    meta = r
                    label = f"{meta.get('name') or 'Unnamed'} — {meta.get('category') or 'Others'}"
                    # Prefer showing Product Type — Brand
                    label = f"{meta.get('name') or 'Unnamed'}"
                    options_map[f"{label}"] = r.get('id')
                
                if not options_map:
                    st.info("✅ All available chemicals are already assigned to this partner.")
                else:
                    st.markdown("**Select chemicals (with TDS) to assign**")
                    sel_labels = st.multiselect(
                        "Chemicals",
                        options=list(options_map.keys()),
                    )
                    
                    if st.button("Assign to Partner", type="primary"):
                        to_add = []
                        for lb in sel_labels:
                            tid = options_map.get(lb)
                            if not tid or tid in already_ids:
                                continue
                            rec = next((r for r in tds_records if r.get('id') == tid), None)
                            if not rec:
                                continue
                            to_add.append({
                                "tds_id": rec.get("id"),
                                "chemical_type_id": rec.get("chemical_type_id"),
                                "name": rec.get("name"),
                                "category": rec.get("category"),
                            })
                        new_list = existing + to_add
                        partner_set_products(partner_obj.get("id"), new_list)
                        st.success("Assigned chemicals to partner")
                        # Reset selection inputs
                        _reset_session_by_prefix(["rem_","add_more_"])
                        st.rerun()

    elif current_partner_tab == "Manage":
        st.subheader("Manage Partners")
        partners = fetch_partners()
        if not partners:
            st.info("No partners found")
        else:
            for p in partners:
                pid = p.get("id")
                with st.expander(f"🤝 {p.get('partner')} ({p.get('partner_country')})", expanded=False):
                    col1, col2 = st.columns([3,2])
                    with col1:
                        e_name = st.text_input("Partner", value=p.get("partner", ""), key=f"pn_{pid}")
                    with col2:
                        e_country = st.selectbox("Country", COUNTRIES, index=(COUNTRIES.index(p.get("partner_country", "")) if p.get("partner_country") in COUNTRIES else 0), key=f"pc_{pid}")

                    # (Actions moved under TDS-backed Products below)

                    st.markdown("---")
                    st.subheader("Assigned TDS-backed Products")
                    assigned = partner_get_products(p)
                    if not assigned:
                        st.caption("No chemicals assigned to this partner.")
                    else:
                        # Group by category for display
                        by_cat_ro: dict[str, list[dict]] = {}
                        for r in assigned:
                            by_cat_ro.setdefault(r.get("category") or "Others", []).append(r)
                        for cat, items in by_cat_ro.items():
                            with st.expander(f"📁 {cat}", expanded=False):
                                for rec in items:
                                    st.write(rec.get("name") or "Unnamed")

                    # 2) Remove link(s) from already linked TDS
                    if assigned:
                        st.markdown("**Remove linked chemicals**")
                        # build label -> index mapping for assigned
                        rem_labels_map = {}
                        for idx, rec in enumerate(assigned):
                            label = rec.get("name") or f"Item {idx+1}"
                            rem_labels_map[f"{label}"] = idx
                        to_remove_labels = st.multiselect(
                            "Select assigned items to remove",
                            list(rem_labels_map.keys()),
                            key=f"rem_{pid}"
                        )
                        if st.button("Remove Selected", key=f"btn_rem_{pid}"):
                            keep = []
                            drop_indices = {rem_labels_map[lbl] for lbl in to_remove_labels}
                            for idx, rec in enumerate(assigned):
                                if idx not in drop_indices:
                                    keep.append(rec)
                            partner_set_products(pid, keep)
                            st.success("Removed selected links")
                            st.rerun()

                    # Add additional chemicals to this partner
                    st.markdown("---")
                    st.subheader("Add Additional Chemical TDS")
                    tds_records_all = list_all_tds()
                    # 3) Only show unlinked TDS for adding
                    current_ids = {it.get('tds_id') for it in assigned if isinstance(it, dict)}
                    unlinked = [r for r in tds_records_all if r.get('id') not in current_ids]
                    
                    
                    opts = {f"{r.get('name') or 'Unnamed'}": r.get('id') for r in unlinked}
                    add_labels = st.multiselect("Select chemicals to add", list(opts.keys()), key=f"add_more_{pid}")
                    if st.button("Add Selected", key=f"btn_add_more_{pid}"):
                        add_items = []
                        for lb in add_labels:
                            tid = opts.get(lb)
                            if tid in current_ids:
                                continue
                            rec = next((r for r in tds_records_all if r.get('id') == tid), None)
                            if rec:
                                add_items.append({
                                    "tds_id": rec.get("id"),
                                    "chemical_type_id": rec.get("chemical_type_id"),
                                    "name": rec.get("name"),
                                    "category": rec.get("category"),
                                })
                        new_list = assigned + add_items
                        partner_set_products(pid, new_list)
                        st.success("Added")
                        _reset_session_by_prefix(["add_more_"])
                        st.rerun()
                    # Compact action buttons placed under TDS-backed Products
                    st.markdown('<div class="partner-actions partner-actions-cta">', unsafe_allow_html=True)
                    btn_col1, btn_col2 = st.columns([1,1])
                    with btn_col1:
                        if st.button("💾 Save", key=f"ps_{pid}"):
                            if not e_name.strip() or not e_country.strip():
                                st.error("Name and country cannot be empty")
                            elif partner_exists(e_name, e_country) and _normalize_partner_name(e_name) != _normalize_partner_name(p.get("partner") or ""):
                                st.error("Another partner already exists with the same name and country")
                            else:
                                # Check for very similar partners (excluding current partner)
                                very_similar = _fuzzy_match_partners(e_name, e_country, threshold=0.9)
                                # Filter out current partner from similar matches
                                very_similar = [s for s in very_similar if s["id"] != pid]
                                
                                if very_similar:
                                    st.error("❌ Cannot update partner: Very similar partner already exists!")
                                    st.write("**Similar partners found:**")
                                    for similar in very_similar:
                                        similarity_percent = int(similar["similarity"] * 100)
                                        st.write(f"• {similar['partner']} ({similar['partner_country']}) - {similarity_percent}% similar")
                                    st.caption("Please use a different name or check if this is the same partner.")
                                else:
                                    update_partner(pid, {"partner": e_name.strip(), "partner_country": e_country.strip()})
                                    st.success("Updated")
                                    st.rerun()
                    with btn_col2:
                        if st.button("🗑️ Delete", key=f"pd_{pid}"):
                            delete_partner(pid)
                            st.success("Deleted")
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    elif current_partner_tab == "View":
        st.subheader("View Partners")
        partners = fetch_partners()
        if not partners:
            st.info("No partners found")
        else:
            # Fetch all TDS once for matching
            try:
                tds_records_all = supabase.table("tds_data").select("id,brand,metadata,chemical_type_id").execute().data or []
            except Exception:
                tds_records_all = []
            # Index by chemical_type_id for quick partner links resolution
            tds_by_type: dict[str, list[dict]] = {}
            try:
                for _tds in tds_records_all:
                    _ctid = (_tds.get("chemical_type_id") or "").strip()
                    if not _ctid:
                        continue
                    tds_by_type.setdefault(_ctid, []).append(_tds)
            except Exception:
                tds_by_type = {}

            # Simple view-only list of partners with their TDS-backed products
            for p in partners:
                pname = (p.get("partner") or "").strip()
                pcountry = (p.get("partner_country") or "").strip()
                pname_l = pname.lower()
                # Build robust tokens for matching (strip parentheses/punctuation)
                import re as _re_pv
                _base_name = _re_pv.sub(r"\(.*?\)", "", pname_l)  # remove parenthetical e.g., (china)
                _base_name = _re_pv.sub(r"[^a-z0-9\s]", " ", _base_name)
                partner_tokens = [t for t in _base_name.split() if len(t) >= 3]

                # Prefer explicit TDS-backed products stored on partner record
                partner_products = (
                    p.get("tds_products")
                    or p.get("products")
                    or (p.get("metadata") or {}).get("tds_products")
                    or []
                )

                matched: list[dict] = []
                if isinstance(partner_products, list) and partner_products:
                    for it in partner_products:
                        try:
                            if not isinstance(it, dict):
                                continue
                            ct_id = (it.get("chemical_type_id") or it.get("type_id") or "").strip()
                            if ct_id and ct_id in tds_by_type:
                                for tds in tds_by_type.get(ct_id) or []:
                                    meta = tds.get("metadata") or {}
                                    matched.append({
                                        "name": meta.get("product_name") or meta.get("generic_product_name") or (tds.get("brand") or "Unnamed"),
                                        "category": meta.get("category") or "Others",
                                        "tds_file_url": meta.get("tds_file_url"),
                                        "tds_file_name": meta.get("tds_file_name"),
                                    })
                            else:
                                # Fallback by name if provided
                                nm = (it.get("name") or "").strip().lower()
                                if nm:
                                    for tds in tds_records_all:
                                        meta = tds.get("metadata") or {}
                                        hay = " ".join([
                                            str(meta.get("product_name") or ""),
                                            str(meta.get("generic_product_name") or ""),
                                            str(tds.get("brand") or ""),
                                        ]).lower()
                                        if nm in hay:
                                            matched.append({
                                                "name": meta.get("product_name") or meta.get("generic_product_name") or (tds.get("brand") or "Unnamed"),
                                                "category": meta.get("category") or "Others",
                                                "tds_file_url": meta.get("tds_file_url"),
                                                "tds_file_name": meta.get("tds_file_name"),
                                            })
                        except Exception:
                            continue
                else:
                    # Fallback: match TDS by supplier/brand using robust token matching
                    for tds in tds_records_all:
                        meta = tds.get("metadata") or {}
                        supplier = (meta.get("supplier_name") or "").strip().lower()
                        brand = (tds.get("brand") or "").strip().lower()
                        hay = f"{supplier} {brand}"
                        hay_norm = _re_pv.sub(r"[^a-z0-9\s]", " ", hay)
                        if pname_l and (pname_l in hay_norm):
                            cond = True
                        else:
                            # token membership
                            cond = any(t in hay_norm for t in partner_tokens)
                        if cond:
                            matched.append({
                                "name": meta.get("product_name") or meta.get("generic_product_name") or (tds.get("brand") or "Unnamed"),
                                "category": meta.get("category") or "Others",
                                "tds_file_url": meta.get("tds_file_url"),
                                "tds_file_name": meta.get("tds_file_name"),
                            })

                # Display partner information directly without view/close buttons
                with st.expander(f"🤝 {pname} ({pcountry})", expanded=False):
                    # Header info (view-only)
                    cols = st.columns([3,2])
                    with cols[0]:
                        st.markdown(f"**Partner:** {pname or '-'}")
                    with cols[1]:
                        st.markdown(f"**Country:** {pcountry or '-'}")

                    st.markdown("---")
                    st.subheader("Assigned TDS-backed Products")
                    # Show only chemicals assigned to this partner (like Manage)
                    assigned_view = partner_get_products(p)
                    if not assigned_view:
                        st.caption("No chemicals assigned to this partner.")
                    else:
                        by_cat_ro: dict[str, list[dict]] = {}
                        for r in assigned_view:
                            by_cat_ro.setdefault(r.get("category") or "Others", []).append(r)
                        for cat, items in by_cat_ro.items():
                            with st.expander(f"📁 {cat}", expanded=False):
                                for rec in items:
                                    st.markdown(f"- {rec.get('name') or 'Unnamed'}")

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - Pricing & Costing Master Data
# ==========================
if st.session_state.get("main_section") == "pricing" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Pricing & Costing Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # Helpers
    def _fetch_partners_simple() -> list[dict]:
        try:
            return supabase.table("partner_data").select("id,partner,partner_country").order("partner").execute().data or []
        except Exception:
            return []

    def _fetch_tds_simple() -> list[dict]:
        try:
            rows = supabase.table("tds_data").select("id,chemical_type_id,brand,metadata").order("created_at", desc=True).execute().data or []
            items = []
            for r in rows:
                meta = r.get("metadata") or {}
                items.append({
                    "id": r.get("id"),
                    "chemical_type_id": r.get("chemical_type_id"),
                    "name": meta.get("product_name") or meta.get("generic_product_name") or (r.get("brand") or "Unnamed"),
                    "category": meta.get("category") or "Others",
                })
            return items
        except Exception:
            return []

    def _fetch_tds_for_partner(partner_id: str) -> list[dict]:
        """Get TDS records assigned to a specific partner"""
        try:
            # Get partner's assigned products - check all possible fields like partner_get_products does
            partner_resp = supabase.table("partner_data").select("metadata").eq("id", partner_id).execute()
            if not partner_resp.data:
                st.error(f"❌ No partner found with ID: {partner_id}")
                return []
            
            partner_data = partner_resp.data[0]
            
            # Get assigned products from metadata field
            assigned_products = []
            try:
                md = partner_data.get("metadata") or {}
                if isinstance(md.get("tds_products"), list):
                    assigned_products = md.get("tds_products") or []
            except Exception:
                pass
            
            if not assigned_products:
                return []
            
            # Get TDS IDs from assigned products
            tds_ids = [p.get("tds_id") for p in assigned_products if p.get("tds_id")]
            if not tds_ids:
                return []
            
            # Fetch TDS records for these IDs
            rows = supabase.table("tds_data").select("id,chemical_type_id,brand,metadata").in_("id", tds_ids).order("created_at", desc=True).execute().data or []
            items = []
            for r in rows:
                meta = r.get("metadata") or {}
                items.append({
                    "id": r.get("id"),
                    "chemical_type_id": r.get("chemical_type_id"),
                    "name": meta.get("product_name") or meta.get("generic_product_name") or (r.get("brand") or "Unnamed"),
                    "category": meta.get("category") or "Others",
                })
            return items
        except Exception:
            return []

    GLOBAL_INCOTERMS = ["FOB", "CIF Mombasa", "SEZ MCF", "Nairobi", "FCA", "Addis Ababa"]
    KENYA_INCOTERMS = ["Kenya", "Nairobi", "FCA Moyale", "Addis"]

    def _incoterm_rows_default():
        rows = []
        for inc in GLOBAL_INCOTERMS + KENYA_INCOTERMS:
            rows.append({"incoterm": inc, "cost_usd": "", "cost_etb": "", "price_usd": "", "price_etb": ""})
        return rows

    def _split_rows(rows: list[dict]):
        global_rows, kenya_rows, other_rows = [], [], []
        try:
            for r in rows or []:
                inc = str(r.get("incoterm") or "").strip()
                if inc in GLOBAL_INCOTERMS:
                    global_rows.append(r)
                elif inc in KENYA_INCOTERMS:
                    kenya_rows.append(r)
                else:
                    other_rows.append(r)
        except Exception:
            pass
        return global_rows, kenya_rows, other_rows

    def _pricing_table_add(partner_id: str, tds_id: str, rows: list[dict]):
        try:
            payload = {
                "partner_id": partner_id,
                "tds_id": tds_id,
                "rows": rows,
            }
            return supabase.table("costing_pricing_data").insert(payload).execute()
        except Exception as e:
            st.error(f"Failed to save pricing: {e}")
            return None

    def _pricing_table_update(pid: str, updates: dict):
        try:
            return supabase.table("costing_pricing_data").update(updates).eq("id", pid).execute()
        except Exception as e:
            st.error(f"Failed to update pricing: {e}")
            return None

    def _pricing_table_delete(pid: str):
        try:
            return supabase.table("costing_pricing_data").delete().eq("id", pid).execute()
        except Exception as e:
            st.error(f"Failed to delete pricing: {e}")
            return None

    def _pricing_fetch_all():
        try:
            return supabase.table("costing_pricing_data").select("*").order("created_at", desc=True).execute().data or []
        except Exception as e:
            st.info("Pricing table not found yet. It will be created when you save your first record.")
            return []

    # Create custom tab navigation with proper change detection
    tab_col1, tab_col2, tab_col3 = st.columns(3)
    
    with tab_col1:
        if st.button("Add", key="pricing_tab_add", type="primary" if st.session_state.get("pricing_current_tab") == "Add" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("pricing_current_tab")
            if previous_tab and previous_tab != "Add" and _has_unsaved_pricing_changes():
                st.session_state["pending_pricing_tab"] = "Add"
                st.rerun()
            else:
                # Clear session when switching to Add tab
                if previous_tab and previous_tab != "Add":
                    _clear_pricing_session()
                st.session_state["pricing_current_tab"] = "Add"
                st.rerun()
    
    with tab_col2:
        if st.button("Manage", key="pricing_tab_manage", type="primary" if st.session_state.get("pricing_current_tab") == "Manage" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("pricing_current_tab")
            if previous_tab and previous_tab != "Manage" and _has_unsaved_pricing_changes():
                st.session_state["pending_pricing_tab"] = "Manage"
                st.rerun()
            else:
                # Clear session when switching to Manage tab
                if previous_tab and previous_tab != "Manage":
                    _clear_pricing_session()
                st.session_state["pricing_current_tab"] = "Manage"
                st.rerun()
    
    with tab_col3:
        if st.button("View", key="pricing_tab_view", type="primary" if st.session_state.get("pricing_current_tab") == "View" else "secondary", use_container_width=True):
            previous_tab = st.session_state.get("pricing_current_tab")
            if previous_tab and previous_tab != "View" and _has_unsaved_pricing_changes():
                st.session_state["pending_pricing_tab"] = "View"
                st.rerun()
            else:
                # Clear session when switching to View tab
                if previous_tab and previous_tab != "View":
                    _clear_pricing_session()
                st.session_state["pricing_current_tab"] = "View"
                st.rerun()
    
    # Handle pending pricing tab changes with confirmation dialog
    if st.session_state.get("pending_pricing_tab"):
        new_tab = st.session_state.get("pending_pricing_tab")
        previous_tab = st.session_state.get("pricing_current_tab")
        
        if previous_tab == "Add":
            st.warning("⚠️ You have unsaved changes in the Add tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_pricing_add", type="primary"):
                    _clear_pricing_session()
                    st.session_state["pricing_current_tab"] = new_tab
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_pricing_add"):
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif previous_tab == "Manage":
            st.warning("⚠️ You have unsaved changes in the Manage tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_pricing_manage", type="primary"):
                    _clear_pricing_session()
                    st.session_state["pricing_current_tab"] = new_tab
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_pricing_manage"):
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
        elif previous_tab == "View":
            st.warning("⚠️ You have unsaved changes in the View tab.")
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("🗑️ Discard & Continue", key="discard_pricing_view", type="primary"):
                    _clear_pricing_session()
                    st.session_state["pricing_current_tab"] = new_tab
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_pricing_view"):
                    st.session_state.pop("pending_pricing_tab")
                    st.rerun()
            with col3:
                st.caption("Your unsaved changes will be lost if you continue.")
            st.stop()
    
    # Get current tab for rendering
    current_pricing_tab = st.session_state.get("pricing_current_tab", "Add")

    # Add
    if current_pricing_tab == "Add":
        colp1, colp2 = st.columns(2)
        partners = _fetch_partners_simple()
        partner_opts = {f"{p.get('partner')} ({p.get('partner_country')})": p.get("id") for p in partners}

        with colp1:
            _partner_placeholder = "— Select —"
            _partner_labels = [_partner_placeholder] + list(partner_opts.keys()) if partner_opts else [_partner_placeholder]
            sel_partner_label = st.selectbox("Partner", _partner_labels, index=0)
        
        # Get selected partner ID
        sel_partner_id = partner_opts.get(sel_partner_label) if sel_partner_label != _partner_placeholder else None
        
        # Get TDS items only for the selected partner
        if sel_partner_id:
            tds_items = _fetch_tds_for_partner(sel_partner_id)
        else:
            tds_items = []
        
        tds_opts = {f"{t.get('name')} — {t.get('category')}": t.get("id") for t in tds_items}

        with colp2:
            _tds_placeholder = "— Select —"
            _tds_labels = [_tds_placeholder] + list(tds_opts.keys()) if tds_opts else [_tds_placeholder]
            sel_tds_label = st.selectbox("Select TDS", _tds_labels, index=0)
            
            # Show message if no TDS available for selected partner
            if sel_partner_label != _partner_placeholder and not tds_items:
                st.info("ℹ️ No chemicals assigned to this partner. Please assign chemicals in Partner Master Data first.")

        # Auto-clear pricing inputs when Partner or TDS selection changes
        _prev_partner = st.session_state.get("pricing_prev_partner_label")
        _prev_tds = st.session_state.get("pricing_prev_tds_label")
        if sel_partner_label != _prev_partner or sel_tds_label != _prev_tds:
            _reset_session_keys(["pricing_rows_add"]) 
            # Bump reset token so all widget keys change and state is flushed
            st.session_state["pricing_form_reset_token"] = str(uuid.uuid4())
            st.session_state["pricing_prev_partner_label"] = sel_partner_label
            st.session_state["pricing_prev_tds_label"] = sel_tds_label
            # Reinitialize default rows for fresh input after change
            st.session_state["pricing_rows_add"] = _incoterm_rows_default()

        # Editable pricing table
        st.markdown("---")
        st.subheader("Pricing & Costing Table")
        
        # Check if both partner and TDS are selected
        sel_partner_id = partner_opts.get(sel_partner_label) if sel_partner_label != _partner_placeholder else None
        sel_tds_id = tds_opts.get(sel_tds_label) if sel_tds_label != _tds_placeholder else None
        both_selected = sel_partner_id and sel_tds_id
        
        if not both_selected:
            st.warning("⚠️ Please select both Partner and TDS to add pricing data")
            st.stop()
        
        if "pricing_rows_add" not in st.session_state:
            st.session_state["pricing_rows_add"] = _incoterm_rows_default()

        rows = st.session_state["pricing_rows_add"]
        _pricing_token = st.session_state.get("pricing_form_reset_token", "0")
        global_rows, kenya_rows, other_rows = _split_rows(rows)

        def _render_rows(prefix: str, rows_list: list[dict]):
            st.caption("Incoterm | Costing USD | Costing ETB | Pricing USD | Pricing ETB")
            for i, r in enumerate(rows_list):
                c1, c2, c3, c4, c5 = st.columns([2,2,2,2,2])
                with c1:
                    st.text_input("Incoterm", value=r.get("incoterm", ""), key=f"{prefix}_{_pricing_token}_inc_{i}")
                with c2:
                    st.text_input("Costing USD", value=r.get("cost_usd", ""), key=f"{prefix}_{_pricing_token}_cu_{i}")
                with c3:
                    st.text_input("Costing ETB", value=r.get("cost_etb", ""), key=f"{prefix}_{_pricing_token}_ce_{i}")
                with c4:
                    st.text_input("Pricing USD", value=r.get("price_usd", ""), key=f"{prefix}_{_pricing_token}_pu_{i}")
                with c5:
                    st.text_input("Pricing ETB", value=r.get("price_etb", ""), key=f"{prefix}_{_pricing_token}_pe_{i}")

        st.markdown("**Global Sourcing (FOB, CIF Mombasa, SEZ MCF, Nairobi, FCA, Addis Ababa)**")
        _render_rows("g", global_rows)

        st.markdown("**Kenya Pricing & Costing (Kenya, Nairobi, FCA Moyale, Addis)**")
        _render_rows("k", kenya_rows)

        # Save combined
        if st.button("💾 Save Pricing", type="primary", key="p_save_add"):
            def _collect(prefix: str, lst: list[dict]):
                out = []
                for i in range(len(lst)):
                    out.append({
                        "incoterm": st.session_state.get(f"{prefix}_{_pricing_token}_inc_{i}") or "",
                        "cost_usd": st.session_state.get(f"{prefix}_{_pricing_token}_cu_{i}") or "",
                        "cost_etb": st.session_state.get(f"{prefix}_{_pricing_token}_ce_{i}") or "",
                        "price_usd": st.session_state.get(f"{prefix}_{_pricing_token}_pu_{i}") or "",
                        "price_etb": st.session_state.get(f"{prefix}_{_pricing_token}_pe_{i}") or "",
                    })
                return out
            out_rows = _collect("g", global_rows) + _collect("k", kenya_rows)
            # Both partner and TDS are already validated above, so we can proceed directly
            resp = _pricing_table_add(sel_partner_id, sel_tds_id, out_rows)
            if resp is not None:
                st.success("✅ Pricing saved")
                # Reset add pricing session state and bump token so widgets clear
                _reset_session_keys(["pricing_rows_add"]) 
                st.session_state["pricing_form_reset_token"] = str(uuid.uuid4())
                st.session_state["pricing_rows_add"] = _incoterm_rows_default()
                st.rerun()
        
        # Add clear session button if there are unsaved changes

    # Manage
    elif current_pricing_tab == "Manage":
        records = _pricing_fetch_all()
        if not records:
            st.info("No pricing records found")
        else:
            # Build partner id -> name map
            _partners_map = {}
            try:
                for p in _fetch_partners_simple():
                    _partners_map[p.get("id")] = p.get("partner")
            except Exception:
                _partners_map = {}
            # Build tds id -> product code (product_name) map
            _tds_name_map = {}
            try:
                _tds_rows = supabase.table("tds_data").select("id,metadata").execute().data or []
                for _r in _tds_rows:
                    _mid = (_r or {}).get("metadata") or {}
                    _tds_name_map[_r.get("id")] = _mid.get("product_name") or _mid.get("generic_product_name")
            except Exception:
                _tds_name_map = {}
            for rec in records:
                rid = rec.get("id")
                partner_id = rec.get("partner_id")
                tds_id = rec.get("tds_id")
                rows = rec.get("rows") or _incoterm_rows_default()

                _pname = _partners_map.get(partner_id, partner_id or "-")
                _prod_code = _tds_name_map.get(tds_id) or "-"
                with st.expander(f"Costing & Pricing — {_pname} — {_prod_code}", expanded=False):
                    # Split rows into groups
                    g_rows, k_rows, o_rows = _split_rows(rows)

                    def _render_manage(prefix: str, rows_list: list[dict], title: str):
                        st.markdown(f"**{title}**")
                        st.caption("Incoterm | Costing USD | Costing ETB | Pricing USD | Pricing ETB")
                        for i, r in enumerate(rows_list):
                            c1, c2, c3, c4, c5 = st.columns([2,2,2,2,2])
                            with c1:
                                st.text_input("Incoterm", value=r.get("incoterm", ""), key=f"pm_inc_{prefix}_{rid}_{i}")
                            with c2:
                                st.text_input("Costing USD", value=r.get("cost_usd", ""), key=f"pm_cu_{prefix}_{rid}_{i}")
                            with c3:
                                st.text_input("Costing ETB", value=r.get("cost_etb", ""), key=f"pm_ce_{prefix}_{rid}_{i}")
                            with c4:
                                st.text_input("Pricing USD", value=r.get("price_usd", ""), key=f"pm_pu_{prefix}_{rid}_{i}")
                            with c5:
                                st.text_input("Pricing ETB", value=r.get("price_etb", ""), key=f"pm_pe_{prefix}_{rid}_{i}")

                    _render_manage("g", g_rows, "Global Sourcing (FOB, CIF Mombasa, SEZ MCF, Nairobi, FCA, Addis Ababa)")
                    _render_manage("k", k_rows, "Kenya Pricing & Costing (Kenya, Nairobi, FCA Moyale, Addis)")

                    mc1, mc2, mc3 = st.columns([1,1,1])
                    with mc1:
                        if st.button("💾 Save", key=f"pm_save_{rid}"):
                            # collect per group
                            def _collect(prefix: str, lst: list[dict]):
                                out = []
                                for i in range(len(lst)):
                                    out.append({
                                        "incoterm": st.session_state.get(f"pm_inc_{prefix}_{rid}_{i}") or "",
                                        "cost_usd": st.session_state.get(f"pm_cu_{prefix}_{rid}_{i}") or "",
                                        "cost_etb": st.session_state.get(f"pm_ce_{prefix}_{rid}_{i}") or "",
                                        "price_usd": st.session_state.get(f"pm_pu_{prefix}_{rid}_{i}") or "",
                                        "price_etb": st.session_state.get(f"pm_pe_{prefix}_{rid}_{i}") or "",
                                    })
                                return out
                            new_rows = _collect("g", g_rows) + _collect("k", k_rows)
                            _pricing_table_update(rid, {"rows": new_rows})
                            st.success("Updated")
                            # Reset manage pricing inputs for this record
                            _reset_session_by_prefix([f"pm_inc_g_{rid}_", f"pm_cu_g_{rid}_", f"pm_ce_g_{rid}_", f"pm_pu_g_{rid}_", f"pm_pe_g_{rid}_", f"pm_inc_k_{rid}_", f"pm_cu_k_{rid}_", f"pm_ce_k_{rid}_", f"pm_pu_k_{rid}_", f"pm_pe_k_{rid}_"]) 
                            st.rerun()
                    with mc2:
                        if st.button("🗑️ Delete", key=f"pm_del_{rid}"):
                            _pricing_table_delete(rid)
                            st.success("Deleted")
                            st.rerun()
                    with mc3:
                        pass

    # View
    elif current_pricing_tab == "View":
        records = _pricing_fetch_all()
        if not records:
            st.info("No pricing records found")
        else:
            _partners_map = {}
            try:
                for p in _fetch_partners_simple():
                    _partners_map[p.get("id")] = p.get("partner")
            except Exception:
                _partners_map = {}
            # Build tds id -> product code (product_name) map
            _tds_name_map_v = {}
            try:
                _tds_rows_v = supabase.table("tds_data").select("id,metadata").execute().data or []
                for _r in _tds_rows_v:
                    _mid = (_r or {}).get("metadata") or {}
                    _tds_name_map_v[_r.get("id")] = _mid.get("product_name") or _mid.get("generic_product_name")
            except Exception:
                _tds_name_map_v = {}
            for rec in records:
                rid = rec.get("id")
                rows = rec.get("rows") or []
                _pname = _partners_map.get(rec.get("partner_id"), rec.get("partner_id") or "-")
                _prod_code = _tds_name_map_v.get(rec.get("tds_id")) or "-"
                with st.expander(f"Costing & Pricing — {_pname} — {_prod_code}", expanded=False):
                    # Split rows similar to Manage view and show as read-only tables
                    g_rows, k_rows, o_rows = _split_rows(rows)

                    def _render_table(title: str, data_rows: list[dict]):
                        st.markdown(f"**{title}**")
                        if not data_rows:
                            st.caption("No rows")
                            st.stop()
                        try:
                            import pandas as _pd
                            df = _pd.DataFrame(data_rows, columns=["incoterm","cost_usd","cost_etb","price_usd","price_etb"])  # type: ignore
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        except Exception:
                            st.caption("Incoterm | Costing USD | Costing ETB | Pricing USD | Pricing ETB")
                            for r in data_rows:
                                st.write(f"- {r.get('incoterm','')} | {r.get('cost_usd','')} | {r.get('cost_etb','')} | {r.get('price_usd','')} | {r.get('price_etb','')}")

                    # First table shows ALL incoterms (Global + Kenya + Others)
                    all_rows = g_rows + k_rows + o_rows
                    _render_table("All Pricing & Costing (FOB, CIF Mombasa, SEZ MCF, Nairobi, FCA, Addis Ababa)", all_rows)
                    
                    # Second table shows only Kenya-specific incoterms
                    _render_table("Kenya Pricing & Costing (Kenya, Nairobi, FCA Moyale, Addis)", k_rows)

    st.markdown('</div>', unsafe_allow_html=True)
