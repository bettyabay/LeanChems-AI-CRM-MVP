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

# Page config
st.set_page_config(page_title="LeanChems PMS", layout="centered")

# Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #f5f9ff; }
    .form-card { background: #fff; padding: 1.25rem 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
    .hint { color: #475569; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# Env and client
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
            },
        )
    except Exception as e:
        st.warning(f"⚠️ Failed to configure Gemini AI: {e}")
        gemini_model = None
else:
    gemini_model = None

# Attempt to restore auth session if present
if "sb_session" in st.session_state:
    try:
        supabase.auth.set_session(
            st.session_state["sb_session"].get("access_token"),
            st.session_state["sb_session"].get("refresh_token"),
        )
    except Exception:
        pass

# Branding and Auth
# Optional logo via env var
LEAN_CHEMS_LOGO_URL = os.getenv("LEAN_CHEMS_LOGO_URL")
MANAGER_EMAILS = {e.strip().lower() for e in (os.getenv("MANAGER_EMAILS", "").split(",")) if e.strip()}
MANAGER_DOMAIN = (os.getenv("MANAGER_DOMAIN") or "").strip().lower()

def get_manager_emails_from_db() -> set:
    try:
        res = supabase.table("managers").select("email").execute()
        emails = { (row.get("email") or "").strip().lower() for row in (res.data or []) if row.get("email") }
        return emails
    except Exception:
        return set()

col_logo, col_title, col_user = st.columns([1, 3, 2])
with col_logo:
    if LEAN_CHEMS_LOGO_URL:
        st.image(LEAN_CHEMS_LOGO_URL, use_container_width=False, width=96)
with col_title:
    st.markdown('<h2 style="color:#0f172a; font-weight:800; margin-bottom:0;">LeanChems Product Management System</h2>', unsafe_allow_html=True)
with col_user:
    # Auth UI
    sb_user = st.session_state.get("sb_user")
    if not sb_user:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password")
            login_clicked = st.form_submit_button("Sign in")
        if login_clicked:
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
                    st.rerun()
                else:
                    st.error("Invalid login response")
            except Exception as e:
                st.error(f"Login failed: {e}")
    else:
        _email_lc = (sb_user.get('email') or '').lower()
        _role = (sb_user.get('role') or '').lower()
        # Check if user is in managers table
        db_manager_emails = get_manager_emails_from_db()
        _is_mgr_display = (_role in {"manager", "admin"}) or (_email_lc in MANAGER_EMAILS) or (_email_lc in db_manager_emails)
        _role_text = "Manager" if _is_mgr_display else "Viewer"
        st.caption(f"Signed in as {sb_user.get('email')} — {_role_text}")
        
        if st.button("Sign out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            for k in ["sb_user", "sb_session"]:
                st.session_state.pop(k, None)
            st.rerun()

# Derived access flags
sb_user = st.session_state.get("sb_user")
user_role = (sb_user or {}).get("role", "viewer")
user_email = ((sb_user or {}).get("email") or "").strip().lower()

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

def get_types_for_category(category: str) -> list[str]:
    """Return product types for a category.

    Priority:
    1) Excel-driven mapping if available (case-insensitive category match)
    2) In-code mapping fallback
    """
    if not category:
        return []

    # 1) Excel mapping (if file loads successfully)
    try:
        excel_map = get_category_type_mapping() or {}
        if excel_map:
            # Exact match first
            if category in excel_map:
                return list(excel_map[category])
            # Case-insensitive match
            cat_lower = category.strip().lower()
            for k, v in excel_map.items():
                if str(k).strip().lower() == cat_lower:
                    return list(v)
    except Exception:
        # Fall through to in-code mapping
        pass

    # 2) Fallback to in-code mapping
    return CATEGORY_TO_TYPES.get(category, [])

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
        
        # Check if response was blocked or failed
        if not response or hasattr(response, 'finish_reason') and response.finish_reason == 2:
            st.warning("⚠️ AI response was blocked. This may be due to content filtering.")
            return None
        
        # Try to get response text safely
        try:
            raw_text = (response.text or "").strip()
        except Exception as text_error:
            st.warning(f"⚠️ Could not extract text from AI response: {text_error}")
            return None
        
        # Parse the response
        extracted_info = {}
        if raw_text:
            lines = raw_text.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
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

# Tabs
tab_add, tab_manage, tab_view, tab_chem_master = st.tabs(["Add Product", "Manage Products", "View Products", "Chemical Master Data"]) 

# UI - Add Product
with tab_add:
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Add Product</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.container():
        st.subheader("Basic Information")
        name = st.text_input("Product Name *", placeholder="Unique product name")
        # Category select or add new (Add-new disables the dropdown)
        col_cat1, col_cat2 = st.columns([3, 1])
        with col_cat1:
            selected_category = st.selectbox(
                "Category *",
                FIXED_CATEGORIES,
                key="category_select",
                disabled=st.session_state.get("add_new_category", False)
            )
        with col_cat2:
            add_new_category = st.checkbox("Add new category", key="add_new_category")
        if add_new_category:
            new_category = st.text_input(
                "New Category Name",
                placeholder="Enter new category name",
                key="new_category_name"
            )
            category = (new_category or "").strip()
        else:
            category = selected_category
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

        # Product Type filtered by selected category (from Excel) + add new
        existing_types = get_types_for_category(category)
        type_options = existing_types  # only types under the selected category
        col_t1, col_t2 = st.columns([3, 1])
        # Per-category keys to avoid stale state across category changes
        key_base = (category or 'none').replace(' ', '_').replace('&', 'and')
        type_checkbox_key = f"add_new_type_{key_base}"
        type_select_key = f"type_select_{key_base}"
        type_input_key = f"new_type_name_{key_base}"
        with col_t1:
            if type_options:
                selected_type = st.selectbox(
                    "Product Type *",
                    options=type_options,
                    key=type_select_key,
                    disabled=st.session_state.get(type_checkbox_key, False)
                )
            else:
                st.info("No mapped product types for this category. Use 'Add new type'.")
                selected_type = ""
        with col_t2:
            add_type_clicked = st.checkbox("Add new type", key=type_checkbox_key)
        new_type = None
        if add_type_clicked:
            new_type = st.text_input("New Type Name", placeholder="Enter new product type", key=type_input_key)
            if new_type:
                selected_type = new_type.strip()

        description = st.text_area("Description", placeholder="Optional description", height=100)

        st.markdown("---")
        st.subheader("Product Status")
        is_leanchems_product = st.selectbox(
            "Is it LeanChems legacy/existing/coming product?",
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
        uploaded_file = st.file_uploader(
            "Upload TDS (PDF/DOCX/Images) — max 10MB *",
            type=ALLOWED_FILE_EXTS
        )

        # AI Processing Button
        if uploaded_file and gemini_model:
            col_ai_process1, col_ai_process2 = st.columns([1, 3])
            with col_ai_process1:
                if st.button("🤖 Extract with AI", type="secondary"):
                    extracted_data = process_tds_with_ai(uploaded_file)
                    if extracted_data:
                        st.session_state["extracted_tds_data"] = extracted_data
                        st.success("✅ AI extraction completed!")
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
        
        # AI TDS Information Extraction fields
        col_ai1, col_ai2 = st.columns(2)
        with col_ai1:
            # Get extracted data from session state
            extracted_data = st.session_state.get("extracted_tds_data", {})
            
            generic_product_name = st.text_input(
                "Generic Product Name", 
                value=extracted_data.get("Generic Product Name", ""),
                placeholder="AI extracted generic name"
            )
            trade_name = st.text_input(
                "Trade Name (Model Name)", 
                value=extracted_data.get("Trade Name", ""),
                placeholder="AI extracted trade/model name"
            )
            supplier_name = st.text_input(
                "Supplier Name", 
                value=extracted_data.get("Supplier Name", ""),
                placeholder="AI extracted supplier name"
            )
            packaging_size_type = st.text_input(
                "Packaging Size & Type", 
                value=extracted_data.get("Packaging Size & Type", ""),
                placeholder="AI extracted packaging info"
            )
        with col_ai2:
            net_weight = st.text_input(
                "Net Weight", 
                value=extracted_data.get("Net Weight", ""),
                placeholder="AI extracted weight"
            )
            hs_code = st.text_input(
                "HS Code", 
                value=extracted_data.get("HS Code", ""),
                placeholder="AI extracted HS code"
            )
            technical_spec = st.text_area(
                "Technical Specification", 
                value=extracted_data.get("Technical Specification", ""),
                placeholder="AI extracted technical specifications", 
                height=100
            )



        submitted = st.button("Save Product", type="primary")

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
            f_ok, f_msg = validate_file(uploaded_file)
            if not f_ok:
                st.error(f_msg)
            else:
                try:
                    # Create a placeholder ID to use for storage path
                    product_id = str(uuid.uuid4())

                    # Upload TDS if provided
                    tds_url, tds_name, tds_size, tds_type = upload_tds_to_supabase(uploaded_file, product_id)

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
                    st.success("✅ Product saved successfully")
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
            res = supabase.table("chemical_types").select("id,generic_name,industry_segments,functional_categories,hs_codes").ilike("generic_name", f"%{q}%").limit(10).execute()
        except Exception:
            # Fallback: exact match only
            res = supabase.table("chemical_types").select("id,generic_name,industry_segments,functional_categories,hs_codes").eq("generic_name", q).limit(10).execute()
        return res.data or []
    except Exception:
        return []

def fetch_chemicals() -> list[dict]:
    try:
        res = supabase.table("chemical_types").select("*").order("generic_name").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Failed to fetch chemicals: {e}")
        return []

def create_chemical(payload: dict):
    return supabase.table("chemical_types").insert(payload).execute()

def update_chemical(chemical_id: str, updates: dict):
    return supabase.table("chemical_types").update(updates).eq("id", chemical_id).execute()

def delete_chemical(chemical_id: str):
    return supabase.table("chemical_types").delete().eq("id", chemical_id).execute()

def get_fallback_chemical_data(chemical_name: str) -> dict:
    """Provide fallback chemical data when AI extraction fails"""
    name_lower = chemical_name.lower()
    
    # Default fallback data
    fallback_data = {
        "generic_name": chemical_name,
        "family": "Chemical compound",
        "synonyms": [],
        "cas_ids": [],
        "hs_codes": [],
        "functional_categories": [],
        "industry_segments": [],
        "key_applications": [],
        "typical_dosage": [],
        "appearance": "Powder or liquid",
        "physical_snapshot": [],
        "compatibilities": [],
        "incompatibilities": [],
        "sensitivities": [],
        "shelf_life_months": 12,
        "storage_conditions": "Store in cool, dry place",
        "packaging_options": ["25 kg bags"],
        "summary_80_20": f"{chemical_name} is a chemical compound used in various industrial applications.",
        "summary_technical": f"Technical specifications for {chemical_name} should be verified from manufacturer data sheets.",
        "data_completeness": 0.3,
    }
    
    # Provide better fallback data for common chemicals
    if "methylcellulose" in name_lower or "methycellulose" in name_lower:
        fallback_data.update({
            "family": "Cellulose ether",
            "synonyms": ["MC", "Methylcellulose"],
            "cas_ids": ["9004-67-5"],
            "hs_codes": [{"region": "WCO", "code": "391290"}],
            "functional_categories": ["Thickener", "Water retention"],
            "industry_segments": ["Dry-mix", "Paint/Coatings"],
            "key_applications": ["Tile adhesive", "Skim coat"],
            "typical_dosage": [{"application": "Tile adhesive", "range": "0.1-0.4% bwoc"}],
            "appearance": "White to off-white powder",
            "physical_snapshot": [{"name": "Moisture", "value": "≤5", "unit": "%", "method": "ASTM E1131"}],
            "compatibilities": ["Cementitious systems"],
            "incompatibilities": ["Strong oxidizers"],
            "sensitivities": ["Salt content", "Alkali level"],
            "shelf_life_months": 24,
            "storage_conditions": "Cool, dry, sealed",
            "packaging_options": ["25 kg bags"],
            "summary_80_20": "Cellulose ether thickener for mortar applications; improves workability and water retention.",
            "summary_technical": "Non-ionic polymer; viscosity grades control open time and sag resistance.",
            "data_completeness": 0.7,
        })
    elif "hpmc" in name_lower or "hydroxypropyl" in name_lower:
        fallback_data.update({
            "family": "Cellulose ether",
            "synonyms": ["HPMC", "Hypromellose"],
            "cas_ids": ["9004-65-3"],
            "hs_codes": [{"region": "WCO", "code": "391290"}],
            "functional_categories": ["Thickener", "Water retention"],
            "industry_segments": ["Dry-mix", "Paint/Coatings"],
            "key_applications": ["Tile adhesive", "Skim coat"],
            "typical_dosage": [{"application": "Tile adhesive", "range": "0.2-0.6% bwoc"}],
            "appearance": "White free-flowing powder",
            "physical_snapshot": [{"name": "Moisture", "value": "≤5", "unit": "%", "method": "ASTM E1131"}],
            "compatibilities": ["Cementitious systems"],
            "incompatibilities": ["Strong oxidizers"],
            "sensitivities": ["Salt content", "Alkali level"],
            "shelf_life_months": 24,
            "storage_conditions": "Cool, dry, sealed",
            "packaging_options": ["25 kg bags"],
            "summary_80_20": "Cellulose ether thickener for mortar/coatings; improves workability and water retention.",
            "summary_technical": "Non-ionic polymer; viscosity grades control open time and sag resistance.",
            "data_completeness": 0.8,
        })
    elif "rdp" in name_lower or "redispersible" in name_lower:
        fallback_data.update({
            "family": "Polymer binder",
            "synonyms": ["RDP", "Redispersible Polymer Powder"],
            "cas_ids": ["9003-20-7"],
            "hs_codes": [{"region": "WCO", "code": "390529"}],
            "functional_categories": ["Binder", "Flexibility enhancer"],
            "industry_segments": ["Dry-mix"],
            "key_applications": ["Tile adhesive", "Skim coat"],
            "typical_dosage": [{"application": "Tile adhesive", "range": "2-5% bwoc"}],
            "appearance": "White/off-white powder",
            "physical_snapshot": [{"name": "Solid content", "value": "≥98", "unit": "%", "method": "Internal"}],
            "compatibilities": ["Cementitious systems"],
            "incompatibilities": ["Strong solvents"],
            "sensitivities": ["Moisture"],
            "shelf_life_months": 12,
            "storage_conditions": "Cool, dry, sealed",
            "packaging_options": ["25 kg bags"],
            "summary_80_20": "Redispersible polymer binder to boost adhesion and flexibility in cement mortars.",
            "summary_technical": "VAE/Veova copolymers; improve tensile strength and crack resistance.",
            "data_completeness": 0.75,
        })
    
    return fallback_data

def analyze_chemical_with_ai(chemical_name: str) -> dict | None:
    if not gemini_model:
        return None
    name = (chemical_name or "").strip()
    if not name:
        return None
    try:
        # Very simple, neutral prompt to avoid content filtering
        prompt = f"""
Analyze this material: "{name}"

Return JSON with this structure:
{{
  "generic_name": "{name}",
  "family": "material type",
  "synonyms": ["alternative names"],
  "cas_ids": ["CAS numbers"],
  "hs_codes": [{{"region": "WCO", "code": "HS code"}}],
  "functional_categories": ["primary functions"],
  "industry_segments": ["main industries"],
  "key_applications": ["primary uses"],
  "typical_dosage": [{{"application": "use case", "range": "typical amount"}}],
  "appearance": "physical description",
  "physical_snapshot": [{{"name": "property name", "value": "property value", "unit": "unit of measure", "method": "test method"}}],
  "compatibilities": ["compatible systems"],
  "incompatibilities": ["incompatible systems"],
  "sensitivities": ["environmental factors"],
  "shelf_life_months": 24,
  "storage_conditions": "storage requirements",
  "packaging_options": ["packaging types"],
  "summary_80_20": "brief description",
  "summary_technical": "technical description",
  "data_completeness": 0.8
}}

Provide reasonable information for each field. Return JSON only.
"""
        response = gemini_model.generate_content(prompt)
        
        # Check if response was blocked or failed
        if not response:
            st.warning("⚠️ No AI response received. Using fallback data.")
            data = get_fallback_chemical_data(name)
        elif hasattr(response, 'finish_reason'):
            if response.finish_reason == 2:
                st.warning("⚠️ AI response was blocked due to content filtering. Using fallback data.")
                data = get_fallback_chemical_data(name)
            elif response.finish_reason == 3:
                st.warning("⚠️ AI response was stopped due to safety concerns. Using fallback data.")
                data = get_fallback_chemical_data(name)
            elif response.finish_reason == 4:
                st.warning("⚠️ AI response was stopped due to recitation. Using fallback data.")
                data = get_fallback_chemical_data(name)
            else:
                st.warning(f"⚠️ AI response had finish reason: {response.finish_reason}. Using fallback data.")
                data = get_fallback_chemical_data(name)
        else:
            # Try to get response text safely
            try:
                raw = (response.text or "").strip()
            except Exception as text_error:
                st.warning(f"⚠️ Could not extract text from AI response: {text_error}. Using fallback data.")
                raw = ""
            
            # Check if we have any content to parse
            if not raw:
                st.warning("⚠️ AI response was empty. Using fallback data.")
                data = get_fallback_chemical_data(name)
            else:
                # Attempt to parse JSON
                import json
                data = {}
                try:
                    data = json.loads(raw)
                except Exception as json_error:
                    st.warning(f"⚠️ Could not parse AI response as JSON: {json_error}. Using fallback data.")
                    # Fallback: provide basic data based on chemical name
                    data = get_fallback_chemical_data(name)
        # Normalize types
        def ensure_list(value):
            if value is None:
                return []
            if isinstance(value, list):
                return value
            if isinstance(value, str):
                return [s.strip() for s in value.split(",") if s.strip()]
            return []

        for key in [
            "synonyms",
            "cas_ids",
            "functional_categories",
            "industry_segments",
            "key_applications",
            "compatibilities",
            "incompatibilities",
            "sensitivities",
            "packaging_options",
        ]:
            data[key] = ensure_list(data.get(key))

        # hs_codes and typical_dosage and physical_snapshot must be arrays of objects
        if not isinstance(data.get("hs_codes"), list):
            data["hs_codes"] = []
        if not isinstance(data.get("typical_dosage"), list):
            data["typical_dosage"] = []
        if not isinstance(data.get("physical_snapshot"), list):
            data["physical_snapshot"] = []

        # Scalars normalization
        data["generic_name"] = (data.get("generic_name") or name).strip()
        data["family"] = (data.get("family") or "").strip()
        data["appearance"] = (data.get("appearance") or "").strip()
        data["storage_conditions"] = (data.get("storage_conditions") or "").strip()
        data["summary_80_20"] = (data.get("summary_80_20") or "").strip()
        data["summary_technical"] = (data.get("summary_technical") or "").strip()
        # Numerics
        try:
            data["shelf_life_months"] = int(data.get("shelf_life_months") or 0)
        except Exception:
            data["shelf_life_months"] = 0
        try:
            dc = float(data.get("data_completeness") or 0.0)
            data["data_completeness"] = max(0.0, min(1.0, dc))
        except Exception:
            data["data_completeness"] = 0.0
        # Heuristic enrichment to ensure non-empty fields for common chemicals
        try:
            name_l = data.get("generic_name", name).lower()
            def ensure(key, value):
                if not data.get(key) or (isinstance(data.get(key), list) and len(data.get(key)) == 0):
                    data[key] = value
            # Redispersible Polymer Powder (RDP)
            if ("redispersible" in name_l and "powder" in name_l) or "rdp" in name_l:
                ensure("family", "Polymer binder")
                ensure("synonyms", ["RDP", "Redispersible Polymer Powder"]) 
                ensure("hs_codes", [{"region": "WCO", "code": "390529"}])
                ensure("functional_categories", ["Binder", "Flexibility enhancer"]) 
                ensure("industry_segments", ["Dry-mix"]) 
                ensure("key_applications", ["Tile adhesive", "Skim coat"]) 
                ensure("typical_dosage", [{"application": "Tile adhesive", "range": "2–5% bwoc"}])
                ensure("appearance", "White/redispersible powder") 
                ensure("physical_snapshot", [{"name": "Solid content", "value": "≥98", "unit": "%", "method": "Internal"}])
                ensure("compatibilities", ["Cementitious systems"]) 
                ensure("incompatibilities", ["Strong solvents"]) 
                ensure("sensitivities", ["Moisture"]) 
                if not data.get("shelf_life_months"):
                    data["shelf_life_months"] = 12
                ensure("storage_conditions", "Cool, dry, sealed") 
                ensure("packaging_options", ["25 kg bags"]) 
                ensure("summary_80_20", "Redispersible polymer binder to boost adhesion/flexibility in cement mortars.") 
                ensure("summary_technical", "VAE/Veova copolymers; improve tensile/peel strength and crack resistance.") 
                if not data.get("data_completeness"):
                    data["data_completeness"] = 0.8
            if "titanium" in name_l and "dioxide" in name_l:
                ensure("family", "Inorganic pigment")
                ensure("synonyms", ["TiO2"])
                ensure("cas_ids", ["13463-67-7"])
                ensure("hs_codes", [{"region": "WCO", "code": "320611"}])
                ensure("functional_categories", ["Pigment", "Opacifier"])
                ensure("industry_segments", ["Paint/Coatings", "Plastics"])
                ensure("key_applications", ["Interior paint", "Plastic masterbatch"])
                ensure("typical_dosage", [{"application": "Interior paint", "range": "15–25%"}])
                ensure("appearance", "White powder")
                ensure("physical_snapshot", [{"name": "Density", "value": "4.2", "unit": "g/cm3", "method": "ISO 787"}])
                ensure("compatibilities", ["Acrylic binders"])
                ensure("incompatibilities", ["Strong acids"])
                ensure("sensitivities", ["Agglomeration"])
                if not data.get("shelf_life_months"):
                    data["shelf_life_months"] = 36
                ensure("storage_conditions", "Dry, covered, avoid contamination")
                ensure("packaging_options", ["25 kg bags", "500 kg big bags"])
                ensure("summary_80_20", "High-opacity white pigment used widely in coatings and plastics.")
                ensure("summary_technical", "Rutile/anatase grades; surface treatment improves dispersion and weathering.")
                if not data.get("data_completeness"):
                    data["data_completeness"] = 0.9
            if ("hydroxypropyl" in name_l and "methylcellulose" in name_l) or "hpmc" in name_l:
                ensure("family", "Cellulose ether")
                ensure("synonyms", ["HPMC", "Hypromellose"])
                ensure("cas_ids", ["9004-65-3"])
                ensure("hs_codes", [{"region": "WCO", "code": "391290"}])
                ensure("functional_categories", ["Thickener", "Water retention"])
                ensure("industry_segments", ["Dry-mix", "Paint/Coatings"])
                ensure("key_applications", ["Tile adhesive", "Skim coat"])
                ensure("typical_dosage", [{"application": "Tile adhesive", "range": "0.2–0.6% bwoc"}])
                ensure("appearance", "White free-flowing powder")
                ensure("physical_snapshot", [{"name": "Moisture", "value": "≤5", "unit": "%", "method": "ASTM E1131"}])
                ensure("compatibilities", ["Cementitious systems"])
                ensure("incompatibilities", ["Strong oxidizers"])
                ensure("sensitivities", ["Salt content", "Alkali level"])
                if not data.get("shelf_life_months"):
                    data["shelf_life_months"] = 24
                ensure("storage_conditions", "Cool, dry, sealed")
                ensure("packaging_options", ["25 kg bags"])
                ensure("summary_80_20", "Cellulose ether thickener for mortar/coatings; improves workability and water retention.")
                ensure("summary_technical", "Non-ionic polymer; viscosity grades control open time and sag.")
                if not data.get("data_completeness"):
                    data["data_completeness"] = 0.85
        except Exception:
            pass
        return data
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
with tab_manage:
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Manage Products</h1>', unsafe_allow_html=True)
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
            filter_leanchems = st.selectbox("LeanChems Chemicals", ["All", "Yes", "No"])
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
                                    st.caption("🏢 LeanChems Product")
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
                                        "Is it LeanChems legacy/existing/coming product?",
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
with tab_view:
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">View Products</h1>', unsafe_allow_html=True)
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
                                st.caption("🏢 LeanChems Product")
                        
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
with tab_chem_master:
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
                    st.write(f"• {d.get('name')} — {d.get('segment') or ''} | {d.get('category') or ''}")

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

        # Editable fields with AI suggestions shown (not prefilled)
        colc1, colc2 = st.columns(2)
        with colc1:
            chem_gen = st.text_input("Generic Name", value="", key="chem_generic", placeholder=extracted.get("generic_name", ""))
            if extracted:
                st.caption(f"AI: {extracted.get('generic_name','')}")
            chem_family = st.text_input("Family", value="", key="chem_family", placeholder=extracted.get("family", ""))
            if extracted:
                st.caption(f"AI: {extracted.get('family','')}")
            chem_syn = st.text_input("Synonyms (comma-separated)", value="", key="chem_syn", placeholder=csv_default(extracted.get("synonyms", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('synonyms', []))}")
            chem_cas = st.text_input("CAS IDs (comma-separated)", value="", key="chem_cas", placeholder=csv_default(extracted.get("cas_ids", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('cas_ids', []))}")
            chem_func = st.text_input("Functional Categories (comma-separated)", value="", key="chem_func", placeholder=csv_default(extracted.get("functional_categories", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('functional_categories', []))}")
            chem_inds = st.text_input("Industry Segments (comma-separated)", value="", key="chem_inds", placeholder=csv_default(extracted.get("industry_segments", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('industry_segments', []))}")
            chem_keys = st.text_input("Key Applications (comma-separated)", value="", key="chem_keys", placeholder=csv_default(extracted.get("key_applications", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('key_applications', []))}")
        with colc2:
            chem_hs_json = st.text_area("HS Codes JSON (array of {region,code})", value="", height=80, key="chem_hs_json", placeholder=_ai_view(extracted.get("hs_codes")))
            if extracted:
                st.caption(f"AI: {_ai_view(extracted.get('hs_codes'))}")
            chem_dosage_json = st.text_area("Typical Dosage JSON (array of {application,range})", value="", height=80, key="chem_dosage_json", placeholder=_ai_view(extracted.get("typical_dosage")))
            if extracted:
                st.caption(f"AI: {_ai_view(extracted.get('typical_dosage'))}")
            chem_phys_json = st.text_area("Physical Snapshot JSON (array of {name,value,unit,method})", value="", height=80, key="chem_phys_json", placeholder=_ai_view(extracted.get("physical_snapshot")))
            if extracted:
                st.caption(f"AI: {_ai_view(extracted.get('physical_snapshot'))}")
            chem_compat = st.text_input("Compatibilities (comma-separated)", value="", key="chem_compat", placeholder=csv_default(extracted.get("compatibilities", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('compatibilities', []))}")
            chem_incompat = st.text_input("Incompatibilities (comma-separated)", value="", key="chem_incompat", placeholder=csv_default(extracted.get("incompatibilities", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('incompatibilities', []))}")
            chem_sens = st.text_input("Sensitivities (comma-separated)", value="", key="chem_sens", placeholder=csv_default(extracted.get("sensitivities", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('sensitivities', []))}")

        colc3, colc4 = st.columns(2)
        with colc3:
            chem_appearance = st.text_input("Appearance", value="", key="chem_appearance", placeholder=extracted.get("appearance", ""))
            if extracted:
                st.caption(f"AI: {extracted.get('appearance','')}")
            chem_storage = st.text_input("Storage Conditions", value="", key="chem_storage", placeholder=extracted.get("storage_conditions", ""))
            if extracted:
                st.caption(f"AI: {extracted.get('storage_conditions','')}")
            chem_pack = st.text_input("Packaging Options (comma-separated)", value="", key="chem_pack", placeholder=csv_default(extracted.get("packaging_options", [])))
            if extracted:
                st.caption(f"AI: {csv_default(extracted.get('packaging_options', []))}")
        with colc4:
            chem_shelf = st.number_input("Shelf Life (months)", min_value=0, max_value=120, value=0, step=1, key="chem_shelf")
            if extracted:
                st.caption(f"AI: {extracted.get('shelf_life_months', 0)}")
            chem_dc = st.slider("Data Completeness", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="chem_dc")
            if extracted:
                st.caption(f"AI: {extracted.get('data_completeness', 0.0)}")
        chem_sum_8020 = st.text_area("Summary 80/20 (5–7 bullets)", value="", height=80, key="chem_8020")
        if extracted:
            st.caption(f"AI: {extracted.get('summary_80_20','')}")
        chem_sum_tech = st.text_area("Summary Technical", value="", height=100, key="chem_sumtech")
        if extracted:
            st.caption(f"AI: {extracted.get('summary_technical','')}")

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
                        arr = parse_json_list(manual)
                        if arr:
                            return arr
                        return ai.get(ai_key) or []

                    payload = {
                        "id": str(uuid.uuid4()),
                        "generic_name": base_name or ai.get("generic_name"),
                        "family": prefer_manual_str(st.session_state.get("chem_family"), "family"),
                        "synonyms": prefer_manual_csv(st.session_state.get("chem_syn"), "synonyms"),
                        "cas_ids": prefer_manual_csv(st.session_state.get("chem_cas"), "cas_ids"),
                        "hs_codes": prefer_manual_jsonarr(st.session_state.get("chem_hs_json"), "hs_codes"),
                        "functional_categories": prefer_manual_csv(st.session_state.get("chem_func"), "functional_categories"),
                        "industry_segments": prefer_manual_csv(st.session_state.get("chem_inds"), "industry_segments"),
                        "key_applications": prefer_manual_csv(st.session_state.get("chem_keys"), "key_applications"),
                        "typical_dosage": prefer_manual_jsonarr(st.session_state.get("chem_dosage_json"), "typical_dosage"),
                        "appearance": prefer_manual_str(st.session_state.get("chem_appearance"), "appearance"),
                        "physical_snapshot": prefer_manual_jsonarr(st.session_state.get("chem_phys_json"), "physical_snapshot"),
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
            search_chem = st.text_input("Search by generic name", placeholder="Start typing...")

            chems = fetch_chemicals()
            filtered_chems = []
            for c in chems:
                if seg_filter and (", ".join(c.get("industry_segments") or [])).lower().find(seg_filter.lower()) < 0:
                    continue
                if cat_filter and (", ".join(c.get("functional_categories") or [])).lower().find(cat_filter.lower()) < 0:
                    continue
                if search_chem and (c.get("generic_name") or "").lower().find(search_chem.lower()) < 0:
                    continue
                filtered_chems.append(c)

            if filtered_chems:
                st.success(f"📋 Found {len(filtered_chems)} chemicals")
            else:
                st.info("No chemicals match the current filters.")

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

        # Export CSV
        if st.button("📊 Export CSV", type="secondary", key="export_csv_view_chemicals"):
            try:
                import pandas as pd
                rows = []
                for c in v_filtered:
                    rows.append({
                        "Generic Name": c.get("generic_name"),
                        "Family": c.get("family"),
                        "Functional Categories": ", ".join(c.get("functional_categories") or []),
                        "Industry Segments": ", ".join(c.get("industry_segments") or []),
                        "Key Applications": ", ".join(c.get("key_applications") or []),
                        "HS Codes": __import__("json").dumps(c.get("hs_codes") or []),
                        "Shelf Life (months)": c.get("shelf_life_months"),
                        "Data Completeness": c.get("data_completeness"),
                    })
                df = pd.DataFrame(rows)
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
                with st.expander(f"🧪 {c.get('generic_name')} — {', '.join(c.get('industry_segments') or [])}"):
                    st.write(f"Family: {c.get('family') or '-'}")
                    st.write(f"Functional Categories: {', '.join(c.get('functional_categories') or []) or '-'}")
                    st.write(f"Industry Segments: {', '.join(c.get('industry_segments') or []) or '-'}")
                    st.write(f"Key Applications: {', '.join(c.get('key_applications') or []) or '-'}")
                    st.write(f"Appearance: {c.get('appearance') or '-'}")
                    st.write(f"Shelf Life (months): {c.get('shelf_life_months') or 0}")
                    st.write(f"Storage: {c.get('storage_conditions') or '-'}")
                    st.write(f"Packaging Options: {', '.join(c.get('packaging_options') or []) or '-'}")
                    st.write(f"Data Completeness: {c.get('data_completeness') or 0.0}")
                    hs_codes = c.get('hs_codes') or []
                    if hs_codes:
                        st.caption(f"HS Codes: {__import__('json').dumps(hs_codes)}")
                    phys = c.get('physical_snapshot') or []
                    if phys:
                        st.caption(f"Physical Snapshot: {__import__('json').dumps(phys)}")
                    dosage = c.get('typical_dosage') or []
                    if dosage:
                        st.caption(f"Typical Dosage: {__import__('json').dumps(dosage)}")

    st.markdown('</div>', unsafe_allow_html=True)

