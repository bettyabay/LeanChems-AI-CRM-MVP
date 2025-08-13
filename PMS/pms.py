import streamlit as st
from dotenv import load_dotenv
import os
from supabase import create_client, Client
import uuid

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
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

ALLOWED_FILE_EXTS = ["pdf", "docx", "doc", "png", "jpg", "jpeg"]
MAX_FILE_MB = 10

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

# Tabs
tab_add, tab_manage, tab_view = st.tabs(["Add Product", "Manage Products", "View Products"])

# UI - Add Product
with tab_add:
    st.markdown('<h1 style="color:#1976d2; font-weight:700;">Add Product</h1>', unsafe_allow_html=True)
    st.markdown('<div class="form-card">', unsafe_allow_html=True)

    with st.form("add_product_form", clear_on_submit=False):
        st.subheader("Basic Information")
        name = st.text_input("Product Name *", placeholder="Unique product name")
        category = st.selectbox("Category *", FIXED_CATEGORIES)

        # Product Type with dynamic + add new
        existing_types = get_distinct_product_types()
        type_options = sorted(set(PREDEFINED_TYPES + existing_types))
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            selected_type = st.selectbox("Product Type *", options=type_options)
        with col_t2:
            add_type_clicked = st.checkbox("Add new type")
        new_type = None
        if add_type_clicked:
            new_type = st.text_input("New Type Name", placeholder="Enter new product type")
            if new_type:
                selected_type = new_type.strip()

        description = st.text_area("Description", placeholder="Optional description", height=100)

        st.markdown("---")
        st.subheader("Technical Data Sheet (TDS)")
        uploaded_file = st.file_uploader(
            "Upload TDS (PDF/DOCX/Images) — max 10MB",
            type=ALLOWED_FILE_EXTS
        )

        st.markdown("---")
        st.subheader("Stakeholders (Optional)")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            suppliers_csv = st.text_input("Suppliers (comma-separated)", placeholder="Supplier A, Supplier B")
        with col_s2:
            partners_csv = st.text_input("Partners (comma-separated)", placeholder="Partner X, Partner Y")

        st.markdown("---")
        st.subheader("Costs (USD / ETB)")
        c1, c2 = st.columns(2)
        with c1:
            fob_cost_usd = st.number_input("FOB Cost USD", min_value=0.0, step=0.01)
            cif_mombasa_cost_usd = st.number_input("CIF Mombasa Cost USD", min_value=0.0, step=0.01)
            sez_mombasa_cost_usd = st.number_input("SEZ Mombasa Cost USD", min_value=0.0, step=0.01)
        with c2:
            fca_moyale_cost_usd = st.number_input("FCA Moyale Cost USD", min_value=0.0, step=0.01)
            client_delivery_cost_etb = st.number_input("Client Delivery Cost ETB", min_value=0.0, step=0.01)
            stock_cost_etb = st.number_input("Stock Cost ETB", min_value=0.0, step=0.01)

        st.markdown("---")
        st.subheader("Prices (USD / ETB)")
        p1, p2 = st.columns(2)
        with p1:
            fob_price_usd = st.number_input("FOB Price USD", min_value=0.0, step=0.01)
            cif_mombasa_price_usd = st.number_input("CIF Mombasa Price USD", min_value=0.0, step=0.01)
            sez_mombasa_price_usd = st.number_input("SEZ Mombasa Price USD", min_value=0.0, step=0.01)
        with p2:
            fca_moyale_price_usd = st.number_input("FCA Moyale Price USD", min_value=0.0, step=0.01)
            client_delivery_price_etb = st.number_input("Client Delivery Price ETB", min_value=0.0, step=0.01)
            stock_price_etb = st.number_input("Stock Price ETB", min_value=0.0, step=0.01)

        st.markdown("---")
        currency_rate = st.number_input("Currency Rate (USD→ETB)", min_value=0.0, value=1.0, step=0.0001, help="Snapshot used for conversions")

        submitted = st.form_submit_button("Save Product", type="primary")

    if submitted:
        # Validate name
        ok, msg = validate_product_name(name)
        if not ok:
            st.error(msg)
        elif name_exists(name):
            st.error("A product with this name already exists")
        else:
            # Validate file
            f_ok, f_msg = validate_file(uploaded_file)
            if not f_ok:
                st.error(f_msg)
            else:
                try:
                    # Build stakeholders JSON
                    stakeholders = []
                    if suppliers_csv.strip():
                        for s in [x.strip() for x in suppliers_csv.split(",") if x.strip()]:
                            stakeholders.append({"type": "Supplier", "name": s})
                    if partners_csv.strip():
                        for p in [x.strip() for x in partners_csv.split(",") if x.strip()]:
                            stakeholders.append({"type": "Partner", "name": p})

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
                        "stakeholders": stakeholders,
                        "fob_cost_usd": fob_cost_usd or None,
                        "cif_mombasa_cost_usd": cif_mombasa_cost_usd or None,
                        "sez_mombasa_cost_usd": sez_mombasa_cost_usd or None,
                        "fca_moyale_cost_usd": fca_moyale_cost_usd or None,
                        "client_delivery_cost_etb": client_delivery_cost_etb or None,
                        "stock_cost_etb": stock_cost_etb or None,
                        "fob_price_usd": fob_price_usd or None,
                        "cif_mombasa_price_usd": cif_mombasa_price_usd or None,
                        "sez_mombasa_price_usd": sez_mombasa_price_usd or None,
                        "fca_moyale_price_usd": fca_moyale_price_usd or None,
                        "client_delivery_price_etb": client_delivery_price_etb or None,
                        "stock_price_etb": stock_price_etb or None,
                        "currency_rate": currency_rate or 1.0,
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

def gather_stakeholder_options(products):
    supplier_set = set()
    partner_set = set()
    for p in products or []:
        for s in (p.get("stakeholders") or []):
            if s.get("type") == "Supplier" and s.get("name"):
                supplier_set.add(s.get("name"))
            if s.get("type") == "Partner" and s.get("name"):
                partner_set.add(s.get("name"))
    return sorted(supplier_set), sorted(partner_set)

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

    # Filters
    colf1, colf2, colf3 = st.columns([2, 2, 1])
    with colf1:
        filter_category = st.selectbox("Filter by Category", ["All"] + FIXED_CATEGORIES)
    with colf2:
        search = st.text_input("Search by name/type", placeholder="Start typing...")
    with colf3:
        only_tds = st.checkbox("With TDS only", value=False)

    products = fetch_products()
    supplier_opts, partner_opts = gather_stakeholder_options(products)
    # Apply filters
    filtered = []
    for p in products:
        if filter_category != "All" and p.get("category") != filter_category:
            continue
        if search:
            if search.lower() not in (p.get("name", "").lower()) and \
               search.lower() not in (p.get("product_type", "").lower()):
                continue
        if only_tds and not p.get("tds_file_url"):
            continue
        filtered.append(p)

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
                                new_tds = st.file_uploader("Replace TDS (optional)", type=ALLOWED_FILE_EXTS, key=f"f_{pid}")

                                # Stakeholders multiselect + add new
                                current_sup_list = [s.get("name") for s in (prod.get("stakeholders") or []) if s.get("type") == "Supplier"]
                                current_par_list = [s.get("name") for s in (prod.get("stakeholders") or []) if s.get("type") == "Partner"]
                                esup_ms = st.multiselect("Suppliers", options=supplier_opts, default=current_sup_list, key=f"supms_{pid}")
                                epar_ms = st.multiselect("Partners", options=partner_opts, default=current_par_list, key=f"parms_{pid}")
                                add_sup = st.text_input("Add Supplier (enter name)", key=f"addsup_{pid}")
                                add_par = st.text_input("Add Partner (enter name)", key=f"addpar_{pid}")
                                if add_sup:
                                    if add_sup not in esup_ms:
                                        esup_ms.append(add_sup)
                                    if add_sup not in supplier_opts:
                                        supplier_opts.append(add_sup)
                                if add_par:
                                    if add_par not in epar_ms:
                                        epar_ms.append(add_par)
                                    if add_par not in partner_opts:
                                        partner_opts.append(add_par)

                                st.markdown("---")
                                cc1, cc2 = st.columns(2)
                                with cc1:
                                    efobc = st.number_input("FOB Cost USD", value=float(prod.get("fob_cost_usd") or 0), step=0.01, key=f"efobc_{pid}")
                                    ecifc = st.number_input("CIF Mombasa Cost USD", value=float(prod.get("cif_mombasa_cost_usd") or 0), step=0.01, key=f"ecifc_{pid}")
                                    esezc = st.number_input("SEZ Mombasa Cost USD", value=float(prod.get("sez_mombasa_cost_usd") or 0), step=0.01, key=f"esezc_{pid}")
                                with cc2:
                                    efcac = st.number_input("FCA Moyale Cost USD", value=float(prod.get("fca_moyale_cost_usd") or 0), step=0.01, key=f"efcac_{pid}")
                                    edelc = st.number_input("Client Delivery Cost ETB", value=float(prod.get("client_delivery_cost_etb") or 0), step=0.01, key=f"edelc_{pid}")
                                    estockc = st.number_input("Stock Cost ETB", value=float(prod.get("stock_cost_etb") or 0), step=0.01, key=f"estockc_{pid}")

                                st.markdown("---")
                                pc1, pc2 = st.columns(2)
                                with pc1:
                                    efobp = st.number_input("FOB Price USD", value=float(prod.get("fob_price_usd") or 0), step=0.01, key=f"efobp_{pid}")
                                    ecifp = st.number_input("CIF Mombasa Price USD", value=float(prod.get("cif_mombasa_price_usd") or 0), step=0.01, key=f"ecifp_{pid}")
                                    esezp = st.number_input("SEZ Mombasa Price USD", value=float(prod.get("sez_mombasa_price_usd") or 0), step=0.01, key=f"esezp_{pid}")
                                with pc2:
                                    efcap = st.number_input("FCA Moyale Price USD", value=float(prod.get("fca_moyale_price_usd") or 0), step=0.01, key=f"efcap_{pid}")
                                    edelp = st.number_input("Client Delivery Price ETB", value=float(prod.get("client_delivery_price_etb") or 0), step=0.01, key=f"edelp_{pid}")
                                    estockp = st.number_input("Stock Price ETB", value=float(prod.get("stock_price_etb") or 0), step=0.01, key=f"estockp_{pid}")

                                prev_rate = float(prod.get("currency_rate") or 1.0)
                                erate = st.number_input("Currency Rate (USD→ETB)", value=prev_rate, step=0.0001, key=f"rate_{pid}")
                                # Warn on >5% deviation from previously saved rate
                                if prev_rate and abs(erate - prev_rate) / prev_rate > 0.05:
                                    st.warning("Rate changed by more than 5% from previously saved value.")

                                # Auto-conversion helpers (USD↔ETB previews)
                                with st.expander("FX helper (preview)", expanded=False):
                                    st.caption("If you change USD/ETB values, use this to preview conversions with current rate.")
                                    usd_val = st.number_input("USD value", value=0.0, step=0.01, key=f"fx_usd_{pid}")
                                    etb_val = st.number_input("ETB value", value=0.0, step=0.01, key=f"fx_etb_{pid}")
                                    colfx1, colfx2 = st.columns(2)
                                    with colfx1:
                                        st.write(f"USD→ETB: {usd_val:.2f} × {erate:.4f} = {usd_val * erate:.2f}")
                                    with colfx2:
                                        st.write(f"ETB→USD: {etb_val:.2f} ÷ {erate:.4f} = {(etb_val / erate) if erate else 0.0:.2f}")

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
                                                "fob_cost_usd": efobc or None,
                                                "cif_mombasa_cost_usd": ecifc or None,
                                                "sez_mombasa_cost_usd": esezc or None,
                                                "fca_moyale_cost_usd": efcac or None,
                                                "client_delivery_cost_etb": edelc or None,
                                                "stock_cost_etb": estockc or None,
                                                "fob_price_usd": efobp or None,
                                                "cif_mombasa_price_usd": ecifp or None,
                                                "sez_mombasa_price_usd": esezp or None,
                                                "fca_moyale_price_usd": efcap or None,
                                                "client_delivery_price_etb": edelp or None,
                                                "stock_price_etb": estockp or None,
                                                "currency_rate": erate or 1.0,
                                            }

                                            # Stakeholders merge (from multiselects)
                                            new_stakeholders = []
                                            for sname in esup_ms:
                                                new_stakeholders.append({"type": "Supplier", "name": sname})
                                            for pname in epar_ms:
                                                new_stakeholders.append({"type": "Partner", "name": pname})
                                            updates["stakeholders"] = new_stakeholders

                                            # TDS upload if provided
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
                            "FCA Moyale Price USD": p.get("fca_moyale_price_usd") or 0,
                            "Client Delivery Price ETB": p.get("client_delivery_price_etb") or 0,
                            "Stock Price ETB": p.get("stock_price_etb") or 0,
                            "Currency Rate": p.get("currency_rate") or 1.0,
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
                        
                        with col2:
                            # TDS status and download
                            if prod.get("tds_file_url"):
                                st.markdown("📄 **TDS:** Available")
                                st.markdown(f"[Download TDS]({prod.get('tds_file_url')})")
                            else:
                                st.markdown("📄 **TDS:** Not available")
                        
                        with col3:
                            if st.button("👁️ View Details", key=f"view_{prod['id']}"):
                                st.session_state[f"viewing_{prod['id']}"] = True

                        # Key prices row
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            fca_price = prod.get("fca_moyale_price_usd")
                            if fca_price:
                                st.metric("FCA Moyale Price USD", f"${fca_price:.2f}")
                            else:
                                st.metric("FCA Moyale Price USD", "Not set")
                        
                        with col_p2:
                            client_price = prod.get("client_delivery_price_etb")
                            if client_price:
                                st.metric("Client Delivery Price ETB", f"ETB {client_price:,.0f}")
                            else:
                                st.metric("Client Delivery Price ETB", "Not set")
                        
                        with col_p3:
                            stock_price = prod.get("stock_price_etb")
                            if stock_price:
                                st.metric("Stock Price ETB", f"ETB {stock_price:,.0f}")
                            else:
                                st.metric("Stock Price ETB", "Not set")

                        # Currency rate info
                        currency_rate = prod.get("currency_rate")
                        if currency_rate and currency_rate != 1.0:
                            st.caption(f"💱 Currency Rate: 1 USD = {currency_rate:.4f} ETB")

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
                                        st.write(f"**File:** {prod.get('tds_file_name')}")
                                        st.write(f"**Size:** {prod.get('tds_file_size', 0) / 1024:.1f} KB")
                                    with col_tds2:
                                        st.write(f"**Type:** {prod.get('tds_file_type')}")
                                        st.markdown(f"[📥 Download TDS]({prod.get('tds_file_url')})")
                                else:
                                    st.write("No TDS file uploaded")
                                
                                # Stakeholders
                                st.markdown("**Stakeholders**")
                                stakeholders = prod.get("stakeholders") or []
                                if stakeholders:
                                    suppliers = [s.get("name") for s in stakeholders if s.get("type") == "Supplier"]
                                    partners = [s.get("name") for s in stakeholders if s.get("type") == "Partner"]
                                    
                                    if suppliers:
                                        st.write(f"**Suppliers:** {', '.join(suppliers)}")
                                    if partners:
                                        st.write(f"**Partners:** {', '.join(partners)}")
                                else:
                                    st.write("No stakeholders defined")
                                
                                # Costs and Prices
                                st.markdown("**Costs & Prices**")
                                col_cp1, col_cp2 = st.columns(2)
                                
                                with col_cp1:
                                    st.markdown("**Costs**")
                                    costs = [
                                        ("FOB Cost USD", prod.get("fob_cost_usd")),
                                        ("CIF Mombasa Cost USD", prod.get("cif_mombasa_cost_usd")),
                                        ("SEZ Mombasa Cost USD", prod.get("sez_mombasa_cost_usd")),
                                        ("FCA Moyale Cost USD", prod.get("fca_moyale_cost_usd")),
                                        ("Client Delivery Cost ETB", prod.get("client_delivery_cost_etb")),
                                        ("Stock Cost ETB", prod.get("stock_cost_etb"))
                                    ]
                                    for label, value in costs:
                                        if value is not None:
                                            if "USD" in label:
                                                st.write(f"{label}: ${value:.2f}")
                                            else:
                                                st.write(f"{label}: ETB {value:,.0f}")
                                        else:
                                            st.write(f"{label}: Not set")
                                
                                with col_cp2:
                                    st.markdown("**Prices**")
                                    prices = [
                                        ("FOB Price USD", prod.get("fob_price_usd")),
                                        ("CIF Mombasa Price USD", prod.get("cif_mombasa_price_usd")),
                                        ("SEZ Mombasa Price USD", prod.get("sez_mombasa_price_usd")),
                                        ("FCA Moyale Price USD", prod.get("fca_moyale_price_usd")),
                                        ("Client Delivery Price ETB", prod.get("client_delivery_price_etb")),
                                        ("Stock Price ETB", prod.get("stock_price_etb"))
                                    ]
                                    for label, value in prices:
                                        if value is not None:
                                            if "USD" in label:
                                                st.write(f"{label}: ${value:.2f}")
                                            else:
                                                st.write(f"{label}: ETB {value:,.0f}")
                                        else:
                                            st.write(f"{label}: Not set")
                                
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
