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
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-2.5-flash')
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
        _is_mgr_display = (_role in {"manager", "admin"}) or (_email_lc in MANAGER_EMAILS)
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
        
        # Parse the response
        extracted_info = {}
        lines = response.text.strip().split('\n')
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                extracted_info[key] = value
        
        return extracted_info
        
    except Exception as e:
        st.error(f"AI extraction error: {str(e)}")
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
tab_add, tab_manage, tab_view = st.tabs(["Add Product", "Manage Products", "View Products"])

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
            if st.button("📊 Export CSV", type="secondary"):
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
