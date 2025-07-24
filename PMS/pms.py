import streamlit as st
from dotenv import load_dotenv
import os
# import openai  # Remove OpenAI
import google.generativeai as genai  # Add Gemini
from supabase import create_client, Client
import pdfplumber
import base64
import tempfile
import uuid
import json
from datetime import datetime

# ---- Custom Background Color ----
st.markdown(
    """
    <style>
    .stApp {
        background-color: #eaf4fb;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Load environment
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))  # Configure Gemini
# Remove OpenAI key usage
# openai.api_key = os.getenv("OPENAI_API_KEY")
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

st.set_page_config(page_title="TDS Product Manager", layout="centered")
st.markdown(
    '<h1 style="color:#1976d2; font-weight: 700;">Leanchems Product Management System (PMS)</h1>',
    unsafe_allow_html=True
)
st.markdown(
    '<div style="font-size:1.2em; color:#333; margin-bottom: 1.5em;">Upload a TDS (Technical Data Sheet) PDF to extract and view product information, or select a product to view its details.</div>',
    unsafe_allow_html=True
)

tabs = st.tabs(["\u2795 Upload TDS", "\U0001F441\uFE0F View Products"])

# -------------------------- Helper Functions --------------------------

def extract_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def ask_gemini(prompt):
      
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content([
            system_msg,
            prompt
        ])
        response_text = response.text.strip()
        # Try to extract JSON if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        return response_text
    except Exception as e:
        return json.dumps({"error": f"Gemini API error: {str(e)}"})

def save_file_to_temp(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.getvalue())
        return tmp.name

def upload_to_supabase(file, name):
    file_bytes = file.getvalue()
    path = f"tds_files/{uuid.uuid4()}.pdf"
    supabase.storage.from_("product-documents").upload(
        path,
        file_bytes,
        {
            "content-type": "application/pdf",
            "x-upsert": "true"
        }
    )
    url = f"https://{os.getenv('SUPABASE_URL').split('//')[1]}/storage/v1/object/public/product-documents/{path}"
    return url

# -------------------------- UPLOAD TAB --------------------------

with tabs[0]:
    with st.form("upload_form"):
        st.subheader("Upload TDS, Import File, or Brochure")

        source_type = st.selectbox("Source Type", ["Supplier", "Customer", "Competitor"])
        stakeholder_name = st.text_input("Stakeholder Name")
        uploaded_pdf = st.file_uploader("Upload Document (PDF)", type="pdf")

        submit = st.form_submit_button("Upload and Process")

    if submit and uploaded_pdf:
        # Save file temporarily
        temp_path = save_file_to_temp(uploaded_pdf)
        raw_text = extract_text_from_pdf(temp_path)

        with st.spinner("\U0001F50D Extracting data using AI..."):
            ai_response = ask_gemini(raw_text)

        # Upload PDF to Supabase Storage
        tds_url = upload_to_supabase(uploaded_pdf, uploaded_pdf.name)

        # Get or create stakeholder
        existing = supabase.table("stakeholders").select("id").eq("name", stakeholder_name).execute()
        stakeholder_id = existing.data[0]['id'] if existing.data else supabase.table("stakeholders").insert({
            "name": stakeholder_name,
            "type": source_type
        }).execute().data[0]['id']

        # Store in uploaded_documents table
        supabase.table("uploaded_documents").insert({
            "file_name": uploaded_pdf.name,
            "uploaded_by": "admin@leanchems.com",  # can make dynamic if auth added
            "source": source_type,
            "stakeholder_id": stakeholder_id,
            "doc_type": "TDS",
            "ocr_text": raw_text,
            "parsed_json": {"ai_summary": ai_response},
        }).execute()

        # Optionally insert into `specific_chemicals` too
        supabase.table("specific_chemicals").insert({
            "name": uploaded_pdf.name.replace(".pdf", ""),
            "supplier_id": stakeholder_id,
            "tds_url": tds_url,
            "source_type": source_type,
            "tech_features": {},
            "quality_params": {}
        }).execute()

        st.success("\u2705 Uploaded and extracted successfully!")
        st.markdown("**AI Extracted Summary:**")
        st.code(ai_response, language="json")

# -------------------------- VIEW TAB --------------------------

with tabs[1]:
    st.subheader("View Uploaded Products")

    chemicals = supabase.table("specific_chemicals").select("id,name").execute().data
    product_dict = {item["name"]: item["id"] for item in chemicals}

    product_options = ["-- Select a product --"] + list(product_dict.keys())
    selected_name = st.selectbox("Select Product", product_options)

    if selected_name == "-- Select a product --":
        st.info("Please select a product to view its TDS and AI-extracted summary.")
    else:
        product_id = product_dict[selected_name]

        # Fetch chemical & document
        chem = supabase.table("specific_chemicals").select("*").eq("id", product_id).execute().data[0]
        doc = supabase.table("uploaded_documents").select("*").eq("file_name", f"{selected_name}.pdf").execute().data

        st.markdown(f"### \U0001F4C4 TDS File")
        st.markdown(f"[Download PDF]({chem['tds_url']})")

        if doc:
            summary = doc[0].get("parsed_json", {}).get("ai_summary", "No summary available.")
            st.markdown("### \U0001F9E0 AI Extracted Info")
            st.code(summary, language="json")
