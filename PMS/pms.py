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
    background: white;
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
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    margin: 0.75rem 0;
    border: 1px solid rgba(147, 197, 253, 0.15);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
}

.feature-box:hover, .form-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
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
    body {
        background-color: #1e1e1e; /* Darker background */
    }
    .stApp {
        background-color: #1e1e1e;
    }
    /* Login screen background in dark mode */
    .stApp:has(.wide-login-container) {
        background: linear-gradient(135deg, #60a5fa 0%, #93c5fd 100%);
    }
    .main .block-container {
        padding-top: 40px;
        padding-right: 60px;
        padding-left: 60px;
        padding-bottom: 40px;
    }
    .css-1d391kg, .css-1v0mbdj {
        background-color: #2c2c2c;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    input {
        border: 1px solid #444;
        background-color: #333;
        color: #f0f0f0;
    }
    button[kind="primary"] {
        background-color: #1a4d7d; /* Dark mode blue */
    }
    button[kind="primary"]:hover {
        background-color: #12395a; /* Darker shade on hover */
    }
    h1, h2, h3, h4 {
        color: #f0f0f0;
    }
    .feature-box {
        background-color: #2c2c2c;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
    .feature-box:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.45);
    }
    .stMarkdown > div > p {
        color: #cccccc;
    }
    .form-card {
        background-color: #2c2c2c;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .hint {
        color: #cccccc;
    }
    /* Force readable text in dark mode (global) */
    .stApp, .stApp * { color: #e5e7eb !important; }
    .stApp a, .stApp a * { color: #93c5fd !important; }
    /* Alerts/notifications */
    .stAlert, [role="alert"], .stInfo, .stSuccess, .stWarning, .stError,
    .stAlert *, [role="alert"] *, .stInfo *, .stSuccess *, .stWarning *, .stError * {
        color: #ffffff !important;
    }
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
""", unsafe_allow_html=True)

# Env and client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
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

# Attempt to restore auth session if present
if "sb_session" in st.session_state:
    try:
        supabase.auth.set_session(
            st.session_state["sb_session"].get("access_token"),
            st.session_state["sb_session"].get("refresh_token"),
        )
    except Exception:
        pass

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
        <p style="color: #718096; margin-top: 1rem; font-size: 1.1rem; text-align: center;">Sign in to access your dashboard</p>
    </div>
    """.format(_get_logo_base64()), unsafe_allow_html=True)
    
    # Login form - always visible
    with st.form("login_form_full", clear_on_submit=False):
        email = st.text_input("📧 Email Address", placeholder="you@example.com", help="Enter your registered email address")
        password = st.text_input("🔐 Password", type="password", placeholder="Enter your password", help="Enter your account password")
        
        # Center the button without using columns
        st.markdown('<div style="text-align: center; margin-top: 1rem;">', unsafe_allow_html=True)
        submit = st.form_submit_button("🚀 Sign In", use_container_width=False, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    if submit:
        if not email or not password:
            st.error("🚫 Please enter both email and password")
        else:
            with st.spinner("🔐 Authenticating..."):
                try:
                    resp = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if resp and getattr(resp, "user", None) and getattr(resp, "session", None):
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
    _is_mgr_display = (_role in {"manager", "admin"}) or (_email_lc in MANAGER_EMAILS) or (_email_lc in db_manager_emails)
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
    "bettyabay@leanchems.com"
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
    
    # bettyabay@leanchems.com has access to all functions
    if user_email_lower == "bettyabay@leanchems.com":
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
elif user_email and user_email in (MANAGER_EMAILS or set()):
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

ALLOWED_FILE_EXTS = ["pdf", "docx", "doc", "png", "jpg", "jpeg"]
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
        res = supabase.table("product_master").select("product_type").execute()
        values = sorted({(row.get("product_type") or "").strip() for row in (res.data or []) if row.get("product_type")})
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

def name_exists(name: str) -> bool:
    res = supabase.table("product_master").select("id").eq("name", name.strip()).limit(1).execute()
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
        supabase.table("tds_sourcing_data").insert(payload).execute()
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
            
        elif file_extension in ['png', 'jpg', 'jpeg']:
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
        - HS Code: [extract HS code if available]
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
        "key": "sourcing_master",
        "title": "📦 Sourcing Master Data",
        "subtitle": "Sourcing Master",
        "description": "Manage sourcing master data (coming soon)",
        "icon": "📦",
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
                st.session_state["main_section"] = item["key"]
                st.rerun()
else:
    st.warning("You don't have access to any modules. Please contact your administrator.")

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

# Access control for new Sourcing Master Data (Coming soon)
if st.session_state.get("main_section") == "sourcing_master" and not has_sourcing_master_access(user_email):
    st.error("🚫 Access Denied: You don't have permission to access Sourcing Master Data. This module is restricted to Iman, Meraf, Alhadi, and Betty Abay.")
    st.info("Please contact your administrator if you believe you should have access to this module.")
    st.stop()

# Enhanced Sourcing sub-navigation when active
if st.session_state.get("main_section") == "sourcing" and has_sourcing_master_access(user_email):
    st.markdown('<div class="form-card" style="margin: 2rem 0;">', unsafe_allow_html=True)
    st.markdown('''
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h3 style="color: #4a5568; font-weight: 600; margin-bottom: 0.5rem;">📋 Sourcing Master Data</h3>
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

# UI - Add Product
if st.session_state.get("main_section") == "sourcing" and st.session_state.get("sourcing_section") == "add" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Add TDS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.container():
        st.subheader("Basic Information")
        name = st.text_input("Product Name *", placeholder="Unique product name")
        # Category select (selection only; no add)
        category = st.selectbox(
            "Chemical Category *",
            FIXED_CATEGORIES,
            key="category_select"
        )
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
            selected_type = st.selectbox(
                "Product Type *",
                options=type_options,
                key=f"type_select_{(category or 'none').replace(' ', '_').replace('&', 'and')}"
            )
        else:
            st.info("No mapped product types for this category in Chemical Master Data.")
            selected_type = ""

        description = st.text_area("Description", placeholder="Optional description", height=100)

        st.markdown("---")
        st.subheader("Product Status")
        is_leanchems_product = st.selectbox(
            "Is it Leanchems legacy/existing/coming product?",
            ["Yes", "No"],
            index=0
        )

        st.markdown("---")
        st.subheader("Source of TDS")
        tds_source = st.selectbox(
            "Where did the TDS come from?",
            ["Supplier", "Customer", "Competitor"],
            index=0
        )

        st.markdown("---")
        st.subheader("Technical Data Sheet (TDS)")
        st.warning("⚠️ TDS upload is required. Products cannot be saved without a TDS file.")
        # Mobile-friendly upload options
        upload_mode = st.radio(
            "Choose upload method",
            options=["File Picker", "Camera", "URL"],
            index=0,
            horizontal=True,
            key="tds_upload_mode"
        )

        uploaded_file = None
        camera_file = None
        url_input = None
        if upload_mode == "File Picker":
            uploaded_file = st.file_uploader(
                "Upload TDS (PDF/DOCX/Images) — max 10MB *",
                type=ALLOWED_FILE_EXTS,
                key="tds_file_picker"
            )
        elif upload_mode == "Camera":
            camera_file = st.camera_input("Capture TDS (photo)", key="tds_camera_input")
        else:
            url_input = st.text_input("TDS File URL (PDF/DOCX/Image)", placeholder="https://...")

        # Helper: download a file from URL and adapt to UploadedFile-like object
        def _download_url_as_upload(url: str):
            try:
                import requests  # type: ignore
                r = requests.get(url, timeout=20)
                if r.status_code != 200:
                    return None, f"Download failed with status {r.status_code}"
                content = r.content or b""
                if not content:
                    return None, "Downloaded file is empty"
                # Determine extension from URL or content-type
                ext = None
                # Try URL extension
                try:
                    from urllib.parse import urlparse
                    path = urlparse(url).path
                    if "." in path:
                        ext = path.split(".")[-1].lower()
                except Exception:
                    ext = None
                if not ext:
                    ctype = r.headers.get("Content-Type", "").lower()
                    mapping = {
                        "application/pdf": "pdf",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
                        "application/msword": "doc",
                        "image/png": "png",
                        "image/jpeg": "jpg",
                    }
                    ext = mapping.get(ctype, None)
                if ext not in ALLOWED_FILE_EXTS:
                    return None, f"Unsupported or unknown file type from URL. Allowed: {', '.join(ALLOWED_FILE_EXTS)}"
                # Build an object with .name, .size, .getvalue()
                class _UrlUploaded:
                    def __init__(self, name: str, data: bytes):
                        self.name = name
                        self._data = data
                        self.size = len(data)
                    def getvalue(self):
                        return self._data
                filename = f"downloaded.{ext}"
                return _UrlUploaded(filename, content), None
            except Exception as e:
                return None, str(e)

        # AI Processing Button
        # Determine a single file-like object for downstream
        effective_file = uploaded_file or camera_file
        if (not effective_file) and url_input:
            url_obj, url_err = _download_url_as_upload(url_input)
            if url_err:
                st.error(f"URL error: {url_err}")
            else:
                effective_file = url_obj

        if effective_file and gemini_model:
            col_ai_process1, col_ai_process2 = st.columns([1, 3])
            with col_ai_process1:
                if st.button("🤖 Extract with AI", type="secondary"):
                    extracted_data = process_tds_with_ai(effective_file)
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
                return
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
            hs_code = st.text_input(
                "HS Code", 
                value=_tds_defs.get("hs_code") or _norm_vals.get("hs_code", ""),
                placeholder="AI extracted HS code",
                key="tds_hs_code"
            )
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
        elif not (uploaded_file or camera_file or (url_input and url_input.strip())):
            st.error("TDS file is required. Please upload, capture, or provide a URL before saving the product.")
        else:
            # Validate file
            # Choose source precedence: file picker > camera > URL
            source_file = uploaded_file or camera_file
            if (not source_file) and url_input:
                source_file, url_err = _download_url_as_upload(url_input)
                if url_err:
                    st.error(f"URL error: {url_err}")
                    st.stop()
            f_ok, f_msg = validate_file(source_file)
            if not f_ok:
                st.error(f_msg)
            else:
                try:
                    # Create a placeholder ID to use for storage path
                    product_id = str(uuid.uuid4())

                    # Upload TDS if provided
                    tds_url, tds_name, tds_size, tds_type = upload_tds_to_supabase(source_file, product_id)

                    # Insert product
                    payload = {
                        "id": product_id,
                        "name": name.strip(),
                        "category": category,
                        "product_type": selected_type.strip(),
                        "description": (description or None),
                        "tds_file_url": tds_url,
                        "tds_file_name": tds_name,
                        "tds_file_size": tds_size,
                        "tds_file_type": tds_type,
                        "tds_source": tds_source,
                        "is_leanchems_product": is_leanchems_product,
                        "generic_product_name": (generic_product_name or "").strip() or None,
                        "trade_name": (trade_name or "").strip() or None,
                        "supplier_name": (supplier_name or "").strip() or None,
                        "packaging_size_type": (packaging_size_type or "").strip() or None,
                        "net_weight": (net_weight or "").strip() or None,
                        "hs_code": (hs_code or "").strip() or None,
                        "technical_spec": (technical_spec or "").strip() or None,
                        "is_active": True,
                    }

                    supabase.table("product_master").insert(payload).execute()
                    # Also create a sourcing entity row
                    chem_type_id = _resolve_chemical_type_id(selected_type, category)
                    brand, grade = _split_brand_grade(trade_name)
                    # Build specs and metadata
                    specs = {}
                    if technical_spec:
                        specs["technical_spec"] = technical_spec
                    metadata = {
                        "generic_product_name": (generic_product_name or None),
                        "packaging": (packaging_size_type or None),
                        "net_weight": (net_weight or None),
                        "hs_code": (hs_code or None),
                        "tds_file_url": tds_url,
                        "product_master_id": product_id,
                    }
                    owner = tds_source  # Supplier / Customer / Competitor
                    ok_entity, err_entity = create_tds_sourcing_entity(
                        chemical_type_id=chem_type_id,
                        brand=(brand or supplier_name or None),
                        grade=grade,
                        owner=owner,
                        source=tds_source,
                        specs=specs,
                        metadata=metadata,
                    )
                    if not ok_entity:
                        st.warning(f"Saved product, but failed to create sourcing entity: {err_entity}")
                    st.success("✅ Record saved successfully")
                except Exception as e:
                    st.error(f"Failed to save product: {e}")

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
            # hs_codes legacy list can live in metadata (keep if present)
            "hs_codes": meta.get("hs_codes") or [],
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
Required JSON schema keys (arrays can be empty):
{{
  "generic_name": string,
  "family": string,
  "synonyms": array,
  "cas_ids": array,
  "hs_codes": array,  // of objects like {{"region":"WCO","code":"HS"}}
  "functional_categories": array,
  "industry_segments": array,
  "key_applications": array,
  "typical_dosage": array, // of objects like {{"application":"","range":""}}
  "appearance": string,
  "physical_snapshot": array, // of objects like {{"name":"","value":"","unit":"","method":""}}
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
 
 Schema:
 {{
   "generic_name": "{name}",
   "family": "material type",
   "synonyms": ["alternative names"],
   "cas_ids": ["CAS numbers"],
   "hs_codes": [{{"region": "WCO", "code": "HS code"}}],
   "functional_categories": ["primary functions"],
   "industry_segments": ["main industries"],
   "key_applications": ["primary uses"],
   "typical_dosage": [{{"application": "use case", "range": "broad % range"}}],
   "appearance": "brief physical description",
   "physical_snapshot": [{{"name": "property", "value": "value", "unit": "unit", "method": "method"}}],
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
        res = supabase.table("product_master").select("*").order("category").order("product_type").order("name").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to fetch products: {e}")
        return []

def update_product(product_id: str, updates: dict):
    return supabase.table("product_master").update(updates).eq("id", product_id).execute()

def name_exists_other(name: str, current_id: str) -> bool:
    res = supabase.table("product_master").select("id").eq("name", name.strip()).neq("id", current_id).limit(1).execute()
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
        st.subheader("📊 Filter Products")
        colf1, colf2, colf3, colf4 = st.columns([2, 2, 2, 1])
        with colf1:
            filter_category = st.selectbox("Filter by Category", ["All"] + FIXED_CATEGORIES)
        with colf2:
            # Product Type Filter
            all_product_types = []
            try:
                res = supabase.table("product_master").select("product_type").execute()
                all_product_types = sorted(list(set([row.get("product_type") for row in (res.data or []) if row.get("product_type")])))
            except Exception:
                pass
            filter_product_type = st.selectbox("Filter by Product Type", ["All"] + all_product_types)
        with colf3:
            # LeanChems Product Filter
            filter_leanchems = st.selectbox("Leanchems Chemicals", ["All", "Yes", "No"])
        with colf4:
            # TDS Filter
            filter_tds = st.selectbox("TDS Status", ["All", "With TDS", "Without TDS"])

        # Search filter
        search = st.text_input("Search by name/type", placeholder="Start typing...")

        products = fetch_products()
        # Apply enhanced filters
        filtered = []
        for p in products:
            # Category filter
            if filter_category != "All" and p.get("category") != filter_category:
                continue
            # Product type filter
            if filter_product_type != "All" and p.get("product_type") != filter_product_type:
                continue
            # LeanChems filter
            if filter_leanchems != "All":
                is_leanchems = p.get("is_leanchems_product", "No")
                if filter_leanchems != is_leanchems:
                    continue
            # TDS filter
            if filter_tds == "With TDS" and not p.get("tds_file_url"):
                continue
            if filter_tds == "Without TDS" and p.get("tds_file_url"):
                continue
            # Search filter
            if search:
                if search.lower() not in (p.get("name", "").lower()) and \
                   search.lower() not in (p.get("product_type", "").lower()):
                    continue
            filtered.append(p)

        # Display filter summary
        if filtered:
            st.success(f"📋 Found {len(filtered)} products matching your filters")
        else:
            st.info("No products match the current filters.")

        if not filtered:
            st.info("No products match the current filters.")
        else:
            # Group by category then type
            by_cat = {}
            for p in filtered:
                by_cat.setdefault(p["category"], {}).setdefault(p["product_type"], []).append(p)

            for cat, types in by_cat.items():
                with st.expander(f"📁 {cat}", expanded=True):
                    for t, items in types.items():
                        st.markdown(f"**🔬 {t}** ({len(items)})")
                        for prod in items:
                            pid = prod["id"]
                            cols = st.columns([3, 2, 2, 2])
                            with cols[0]:
                                st.write(f"• {prod.get('name')}")
                                # Show LeanChems status
                                leanchems_status = prod.get("is_leanchems_product", "No")
                                if leanchems_status == "Yes":
                                    st.caption("🏢 Leanchems Product")
                            with cols[1]:
                                st.write("TDS: "+ ("✅" if prod.get("tds_file_url") else "❌"))
                            with cols[2]:
                                if prod.get("tds_file_url"):
                                    st.markdown(f"[Download TDS]({prod.get('tds_file_url')})")
                            with cols[3]:
                                if st.button("✏️ Edit", key=f"edit_{pid}"):
                                    st.session_state[f"editing_{pid}"] = True

                            if st.session_state.get(f"editing_{pid}"):
                                with st.expander(f"Edit: {prod.get('name')}", expanded=True):
                                    # Editable fields
                                    ename = st.text_input("Name", value=prod.get("name", ""), key=f"n_{pid}")
                                    ecat = st.selectbox("Category", FIXED_CATEGORIES, index=FIXED_CATEGORIES.index(prod.get("category")), key=f"c_{pid}")
                                    # product type: choose existing or new free text
                                    etype = st.text_input("Product Type", value=prod.get("product_type", ""), key=f"t_{pid}")
                                    edesc = st.text_area("Description", value=prod.get("description") or "", key=f"d_{pid}")
                                    
                                    # LeanChems Product Status
                                    eleanchems = st.selectbox(
                                        "Is it Leanchems legacy/existing/coming product?",
                                        ["Yes", "No"],
                                        index=0 if prod.get("is_leanchems_product") == "Yes" else 1,
                                        key=f"leanchems_{pid}"
                                    )
                                    
                                    # Multiple TDS Files Upload (Manage Products only)
                                    st.markdown("---")
                                    st.subheader("📎 Multiple TDS Files")
                                    st.info("💡 You can upload multiple TDS files for this product. Each file will be stored separately.")
                                    
                                    # Show existing TDS files
                                    existing_tds_files = prod.get("additional_tds_files", [])
                                    if existing_tds_files:
                                        st.write("**Current TDS Files:**")
                                        for i, tds_file in enumerate(existing_tds_files):
                                            col_tds1, col_tds2, col_tds3 = st.columns([3, 1, 1])
                                            with col_tds1:
                                                st.write(f"📄 {tds_file.get('name', 'Unknown file')}")
                                            with col_tds2:
                                                st.write(f"{tds_file.get('size', 0) / 1024:.1f} KB")
                                            with col_tds3:
                                                if st.button(f"🗑️ Remove", key=f"remove_tds_{pid}_{i}"):
                                                    # Remove file from list
                                                    existing_tds_files.pop(i)
                                                    # Update product
                                                    try:
                                                        update_product(pid, {"additional_tds_files": existing_tds_files})
                                                        st.success("File removed successfully!")
                                                        st.rerun()
                                                    except Exception as e:
                                                        st.error(f"Failed to remove file: {e}")
                                    
                                    # Upload new TDS files
                                    new_tds_files = st.file_uploader(
                                        "Upload Additional TDS Files (optional)", 
                                        type=ALLOWED_FILE_EXTS, 
                                        accept_multiple_files=True,
                                        key=f"multi_tds_{pid}"
                                    )
                                    
                                    # Replace main TDS (single file)
                                    st.markdown("---")
                                    st.subheader("🔄 Replace Main TDS")
                                    new_tds = st.file_uploader("Replace Main TDS (optional)", type=ALLOWED_FILE_EXTS, key=f"f_{pid}")

                                    # Actions
                                    ac1, ac2 = st.columns(2)
                                    with ac1:
                                        if st.button("💾 Save", key=f"save_{pid}"):
                                            # Validations
                                            n_ok, n_msg = validate_product_name(ename)
                                            if not n_ok:
                                                st.error(n_msg)
                                            elif name_exists_other(ename, pid):
                                                st.error("Another product already uses this name")
                                            else:
                                                # Build updates
                                                updates = {
                                                    "name": ename.strip(),
                                                    "category": ecat,
                                                    "product_type": etype.strip() or prod.get("product_type"),
                                                    "description": edesc or None,
                                                    "is_leanchems_product": eleanchems,
                                                }

                                                # Handle multiple TDS files upload
                                                if new_tds_files:
                                                    additional_files = existing_tds_files.copy()
                                                    for uploaded_file in new_tds_files:
                                                        # Validate file
                                                        okf, msgf = validate_file(uploaded_file)
                                                        if not okf:
                                                            st.error(f"File {uploaded_file.name}: {msgf}")
                                                            continue
                                                        
                                                        # Upload to Supabase
                                                        try:
                                                            url, fname, fsize, ftype = upload_tds_to_supabase(uploaded_file, pid)
                                                            additional_files.append({
                                                                "url": url,
                                                                "name": fname,
                                                                "size": fsize,
                                                                "type": ftype,
                                                                "uploaded_at": datetime.utcnow().isoformat() + "Z"
                                                            })
                                                        except Exception as e:
                                                            st.error(f"Failed to upload {uploaded_file.name}: {e}")
                                                    
                                                    updates["additional_tds_files"] = additional_files

                                                # TDS upload if provided (main TDS)
                                                if new_tds is not None:
                                                    okf, msgf = validate_file(new_tds)
                                                    if not okf:
                                                        st.error(msgf)
                                                    else:
                                                        url, fname, fsize, ftype = upload_tds_to_supabase(new_tds, pid)
                                                        updates.update({
                                                            "tds_file_url": url,
                                                            "tds_file_name": fname,
                                                            "tds_file_size": fsize,
                                                            "tds_file_type": ftype,
                                                        })

                                                # Append version history entry
                                                updates["version_history"] = build_version_entry(prod, updates)

                                                try:
                                                    update_product(pid, updates)
                                                    st.success("✅ Updated")
                                                    st.session_state.pop(f"editing_{pid}", None)
                                                    st.rerun()
                                                except Exception as e:
                                                    st.error(f"Failed to update: {e}")

                                    with ac2:
                                        if st.button("❌ Cancel", key=f"cancel_{pid}"):
                                            st.session_state.pop(f"editing_{pid}", None)

    st.markdown('</div>', unsafe_allow_html=True)

# UI - View Products
if st.session_state.get("main_section") == "sourcing" and st.session_state.get("sourcing_section") == "view" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">View TDS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    # Category selection
    st.subheader("Select Category to View Products")
    selected_category = st.selectbox(
        "Choose Category",
        FIXED_CATEGORIES,
        key="view_category_select"
    )

    # Search within category
    search_view = st.text_input(
        "Search products in this category",
        placeholder="Search by name or type...",
        key="view_search"
    )

    # Fetch products for selected category
    try:
        category_products = supabase.table("product_master").select("*").eq("category", selected_category).order("product_type").order("name").execute()
        products_list = category_products.data or []
    except Exception as e:
        st.error(f"Failed to fetch products: {e}")
        products_list = []

    # Filter by search
    if search_view:
        filtered_products = [
            p for p in products_list 
            if search_view.lower() in p.get("name", "").lower() or 
               search_view.lower() in p.get("product_type", "").lower()
        ]
    else:
        filtered_products = products_list

    if not filtered_products:
        st.info(f"📭 No products found in {selected_category} category.")
        st.markdown(f"💡 [Go to Add Product tab](#) to add your first product in this category.")
    else:
        # Group by product type
        by_type = {}
        for p in filtered_products:
            ptype = p.get("product_type", "Unknown")
            by_type.setdefault(ptype, []).append(p)

        # Export button
        col_export1, col_export2 = st.columns([1, 3])
        with col_export1:
            if st.button("📊 Export CSV", type="secondary", key="export_csv_view_products"):
                try:
                    import pandas as pd
                    # Prepare data for export
                    export_data = []
                    for p in filtered_products:
                        export_data.append({
                            "Product Name": p.get("name"),
                            "Product Type": p.get("product_type"),
                            "Description": p.get("description") or "",
                            "TDS File": p.get("tds_file_name") or "No TDS",
                            "Created": p.get("created_at", ""),
                            "Last Updated": p.get("updated_at", "")
                        })
                    
                    df = pd.DataFrame(export_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"{selected_category}_products_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Export failed: {e}")

        st.markdown(f"**Found {len(filtered_products)} products in {selected_category}**")

        # Display products grouped by type
        for ptype, products in by_type.items():
            with st.expander(f"🔬 {ptype} ({len(products)} products)", expanded=True):
                for prod in products:
                    # Product card
                    with st.container():
                        st.markdown("---")
                        
                        # Main info row
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.markdown(f"**{prod.get('name')}**")
                            if prod.get("description"):
                                st.caption(prod.get("description"))
                            # Show LeanChems status
                            leanchems_status = prod.get("is_leanchems_product", "No")
                            if leanchems_status == "Yes":
                                st.caption("🏢 Leanchems Product")
                        
                        with col2:
                            # TDS status and download
                            if prod.get("tds_file_url"):
                                st.markdown("📄 **TDS:** Available")
                                st.markdown(f"[Download TDS]({prod.get('tds_file_url')})")
                                # Show additional TDS files count
                                additional_files = prod.get("additional_tds_files", [])
                                if additional_files:
                                    st.caption(f"📎 +{len(additional_files)} additional files")
                            else:
                                st.markdown("📄 **TDS:** Not available")
                        
                        with col3:
                            if st.button("👁️ View Details", key=f"view_{prod['id']}"):
                                st.session_state[f"viewing_{prod['id']}"] = True

                        # View Details Modal
                        if st.session_state.get(f"viewing_{prod['id']}"):
                            with st.expander(f"📋 Full Details: {prod.get('name')}", expanded=True):
                                st.markdown("**Product Information**")
                                st.write(f"**Category:** {prod.get('category')}")
                                st.write(f"**Product Type:** {prod.get('product_type')}")
                                if prod.get("description"):
                                    st.write(f"**Description:** {prod.get('description')}")
                                
                                # TDS Information
                                st.markdown("**Technical Data Sheet**")
                                if prod.get("tds_file_url"):
                                    col_tds1, col_tds2 = st.columns(2)
                                    with col_tds1:
                                        st.write(f"**Main TDS File:** {prod.get('tds_file_name')}")
                                        st.write(f"**Size:** {prod.get('tds_file_size', 0) / 1024:.1f} KB")
                                    with col_tds2:
                                        st.write(f"**Type:** {prod.get('tds_file_type')}")
                                        st.markdown(f"[📥 Download Main TDS]({prod.get('tds_file_url')})")
                                else:
                                    st.write("No main TDS file uploaded")
                                
                                # Additional TDS Files
                                additional_files = prod.get("additional_tds_files", [])
                                if additional_files:
                                    st.markdown("**Additional TDS Files:**")
                                    for i, tds_file in enumerate(additional_files):
                                        col_add1, col_add2 = st.columns([3, 1])
                                        with col_add1:
                                            st.write(f"📄 {tds_file.get('name', 'Unknown file')}")
                                            if tds_file.get('uploaded_at'):
                                                st.caption(f"Uploaded: {tds_file.get('uploaded_at')[:19].replace('T', ' ')}")
                                        with col_add2:
                                            st.write(f"{tds_file.get('size', 0) / 1024:.1f} KB")
                                            st.markdown(f"[📥 Download]({tds_file.get('url')})")
                                
                                # Version History
                                st.markdown("**Version History**")
                                version_history = prod.get("version_history") or []
                                if version_history:
                                    for i, entry in enumerate(reversed(version_history[-5:])):  # Show last 5 entries
                                        ts = entry.get("ts", "")
                                        changed = entry.get("changed", {})
                                        if ts:
                                            st.caption(f"**{ts[:19].replace('T', ' ')}**")
                                        if changed:
                                            changes_text = ", ".join([f"{k}: {v}" for k, v in changed.items()])
                                            st.write(f"Changes: {changes_text}")
                                else:
                                    st.write("No version history available")
                                
                                # Close button
                                if st.button("❌ Close Details", key=f"close_{prod['id']}"):
                                    st.session_state.pop(f"viewing_{prod['id']}", None)

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================
# UI - Chemical Master Data
# ==========================
if st.session_state.get("main_section") == "chemical" and has_chemical_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Chemical Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    sub_add, sub_manage, sub_view = st.tabs(["Add Chemical", "Manage Chemicals", "View Chemicals"])

    # -------- Add Chemical --------
    with sub_add:
        st.subheader("Add Chemical")
        if gemini_model:
            st.caption("Type a chemical name and press Enter to analyze with AI and check duplicates.")
        else:
            st.caption("Type a chemical name and press Enter to check duplicates. AI analysis is not available.")

        # Mapping selects at the top (before Type Chemical Name)
        st.markdown("---")
        st.caption("Select Category and Product Type from mapping")
        selected_segment = st.selectbox(
            "Category",
            options=FIXED_CATEGORIES,
            key="chem_seg_select"
        )
        add_new_seg = st.checkbox("Add new category", key="chem_add_new_seg")
        if add_new_seg:
            new_seg = st.text_input("New Category Name", key="chem_new_seg")
            if new_seg:
                selected_segment = new_seg.strip()

        # Persist selections for save logic (no direct widget key to avoid conflicts)
        st.session_state["chem_selected_category"] = selected_segment
        st.write(f"Selected Category: {selected_segment or '-'}")

        with st.form("chem_add_form", clear_on_submit=False):
            chem_name_input = st.text_input("Type Chemical Name:", placeholder="e.g., Redispersible Polymer Powder")
            if gemini_model:
                analyze_submit = st.form_submit_button("Analyze & Prefill")
            else:
                analyze_submit = st.form_submit_button("Check Duplicates")

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
        chem_sum_8020 = st.text_area("Summary 80/20 (5–7 bullets)", value=extracted.get("summary_80_20", ""), height=80, key="chem_8020")
        # 2) Synonyms
        chem_syn = st.text_input("Synonyms (comma-separated)", value=csv_default(extracted.get("synonyms", [])), key="chem_syn")
        # 3) Family
        chem_family = st.text_input("Family", value=extracted.get("family", ""), key="chem_family")
        # 4) Generic Name
        chem_gen = st.text_input("Generic Name", value=extracted.get("generic_name", ""), key="chem_generic")
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
        chem_hs_codes = st.text_input("HS Codes", value=_hs_codes_as_csv(), key="chem_hs_codes")
        # 6) CAS IDs
        chem_cas = st.text_input("CAS IDs", value=csv_default(extracted.get("cas_ids", [])), key="chem_cas")
        # 7) Summary Technical
        chem_sum_tech = st.text_area("Summary Technical", value=extracted.get("summary_technical", ""), height=100, key="chem_sumtech")
        # 8) Functional Categories
        chem_func = st.text_input("Functional Categories", value=csv_default(extracted.get("functional_categories", [])), key="chem_func")
        # 9) Industry Segments
        chem_inds = st.text_input("Industry Segments", value=csv_default(extracted.get("industry_segments", [])), key="chem_inds")
        # 10) Key Applications
        chem_keys = st.text_input("Key Applications", value=csv_default(extracted.get("key_applications", [])), key="chem_keys")
        # 11) Typical Dosage
        chem_dosage_json = st.text_area("Typical Dosage", value=_ai_list_as_lines(extracted.get("typical_dosage")) if extracted else "", height=80, key="chem_dosage_json")
        # 12) Physical Snapshot
        chem_phys_json = st.text_area("Physical Snapshot", value=_ai_list_as_lines(extracted.get("physical_snapshot")) if extracted else "", height=80, key="chem_phys_json")
        # 13) Compatibilities
        chem_compat = st.text_input("Compatibilities", value=csv_default(extracted.get("compatibilities", [])), key="chem_compat")
        # 14) Incompatibilities
        chem_incompat = st.text_input("Incompatibilities", value=csv_default(extracted.get("incompatibilities", [])), key="chem_incompat")
        # 15) Sensitivities
        chem_sens = st.text_input("Sensitivities", value=csv_default(extracted.get("sensitivities", [])), key="chem_sens")
        # 16) Appearance
        chem_appearance = st.text_input("Appearance", value=extracted.get("appearance", ""), key="chem_appearance")
        # 17) Storage Conditions
        chem_storage = st.text_input("Storage Conditions", value=extracted.get("storage_conditions", ""), key="chem_storage")
        # 18) Packaging Options
        chem_pack = st.text_input("Packaging Options", value=csv_default(extracted.get("packaging_options", [])), key="chem_pack")
        # 19) Shelf Life (months)
        chem_shelf = st.number_input("Shelf Life (months)", min_value=0, max_value=120, value=int(extracted.get("shelf_life_months", 0) if extracted else 0), step=1, key="chem_shelf")
        # 20) Data Completeness
        chem_dc = st.slider("Data Completeness", min_value=0.0, max_value=1.0, value=float(extracted.get("data_completeness", 0.0) if extracted else 0.0), step=0.05, key="chem_dc")

        # Show one-line source indicator
        if extracted:
            src = st.session_state.get("chem_ai_source")
            if src:
                st.caption(f"Source: {src}")

        if st.button("Save Chemical", type="primary"):
            # Basic validations
            base_name = normalize_chemical_name(st.session_state.get("chem_generic", ""))
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
                        "family": prefer_manual_str(st.session_state.get("chem_family"), "family"),
                        "synonyms": prefer_manual_csv(st.session_state.get("chem_syn"), "synonyms"),
                        "cas_ids": prefer_manual_csv(st.session_state.get("chem_cas"), "cas_ids"),
                        "hs_codes": (
                            [
                                {"region": "WCO", "code": code}
                                for code in parse_csv_list(st.session_state.get("chem_hs_codes"))
                            ]
                            or ai.get("hs_codes")
                            or []
                        ),
                        "functional_categories": prefer_manual_csv(st.session_state.get("chem_func"), "functional_categories"),
                        "industry_segments": prefer_manual_csv(st.session_state.get("chem_inds"), "industry_segments"),
                        "key_applications": prefer_manual_csv(st.session_state.get("chem_keys"), "key_applications"),
                        "typical_dosage": (
                            _parse_kv_lines(st.session_state.get("chem_dosage_json"))
                            or prefer_manual_jsonarr(st.session_state.get("chem_dosage_json"), "typical_dosage")
                        ),
                        "appearance": prefer_manual_str(st.session_state.get("chem_appearance"), "appearance"),
                        "physical_snapshot": (
                            _parse_kv_lines(st.session_state.get("chem_phys_json"))
                            or prefer_manual_jsonarr(st.session_state.get("chem_phys_json"), "physical_snapshot")
                        ),
                        "compatibilities": prefer_manual_csv(st.session_state.get("chem_compat"), "compatibilities"),
                        "incompatibilities": prefer_manual_csv(st.session_state.get("chem_incompat"), "incompatibilities"),
                        "sensitivities": prefer_manual_csv(st.session_state.get("chem_sens"), "sensitivities"),
                        "shelf_life_months": int(st.session_state.get("chem_shelf") or ai.get("shelf_life_months") or 0),
                        "storage_conditions": prefer_manual_str(st.session_state.get("chem_storage"), "storage_conditions"),
                        "packaging_options": prefer_manual_csv(st.session_state.get("chem_pack"), "packaging_options"),
                        "summary_80_20": prefer_manual_str(st.session_state.get("chem_8020"), "summary_80_20"),
                        "summary_technical": prefer_manual_str(st.session_state.get("chem_sumtech"), "summary_technical"),
                        "data_completeness": float(st.session_state.get("chem_dc") or ai.get("data_completeness") or 0.0),
                    }
                    create_chemical(payload)
                    st.success("✅ Chemical saved successfully")
                except Exception as e:
                    st.error(f"Failed to save chemical: {e}")

    # -------- Manage Chemicals --------
    with sub_manage:
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
                with st.expander(f"🧪 {chem.get('generic_name')}", expanded=False):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        ename = st.text_input("Generic Name", value=chem.get("generic_name", ""), key=f"cn_{cid}")
                        efamily = st.text_input("Family", value=chem.get("family", ""), key=f"cf_{cid}")
                        esyn = st.text_input("Synonyms (comma-separated)", value=", ".join(chem.get("synonyms") or []), key=f"csy_{cid}")
                        ecas = st.text_input("CAS IDs (comma-separated)", value=", ".join(chem.get("cas_ids") or []), key=f"cca_{cid}")
                    with ec2:
                        ehs_json = st.text_area("HS Codes JSON", value=(__import__("json").dumps(chem.get("hs_codes")) if chem.get("hs_codes") else ""), height=70, key=f"ch_{cid}")
                        efunc = st.text_input("Functional Categories (comma-separated)", value=", ".join(chem.get("functional_categories") or []), key=f"cc_{cid}")
                        eind = st.text_input("Industry Segments (comma-separated)", value=", ".join(chem.get("industry_segments") or []), key=f"ci_{cid}")
                    ekeys = st.text_input("Key Applications (comma-separated)", value=", ".join(chem.get("key_applications") or []), key=f"cak_{cid}")
                    edosage_json = st.text_area("Typical Dosage JSON", value=(__import__("json").dumps(chem.get("typical_dosage")) if chem.get("typical_dosage") else ""), height=70, key=f"cdj_{cid}")
                    eappearance = st.text_input("Appearance", value=chem.get("appearance", ""), key=f"cap_{cid}")
                    ephys_json = st.text_area("Physical Snapshot JSON", value=(__import__("json").dumps(chem.get("physical_snapshot")) if chem.get("physical_snapshot") else ""), height=70, key=f"cps_{cid}")
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
                                        "hs_codes": parse_json_list(ehs_json),
                                        "functional_categories": [s.strip() for s in efunc.split(",") if s.strip()],
                                        "industry_segments": [s.strip() for s in eind.split(",") if s.strip()],
                                        "key_applications": [s.strip() for s in ekeys.split(",") if s.strip()],
                                        "typical_dosage": parse_json_list(edosage_json),
                                        "appearance": eappearance.strip() or None,
                                        "physical_snapshot": parse_json_list(ephys_json),
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
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to update: {e}")
                    with colb2:
                        if st.button("🗑️ Delete", key=f"cdel_{cid}"):
                            try:
                                delete_chemical(cid)
                                st.success("Deleted")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to delete: {e}")

    # -------- View Chemicals --------
    with sub_view:
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
                        st.write(f"{label}: {_format_chem_field(c.get(key))}")

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
if st.session_state.get("main_section") == "sourcing_master" and has_sourcing_master_access(user_email):
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Sourcing Master Data</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)
    st.info("🚧 Coming soon")
    st.markdown('</div>', unsafe_allow_html=True)
