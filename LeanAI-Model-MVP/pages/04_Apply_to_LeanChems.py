import os
import json
import uuid
import datetime
import streamlit as st
from pathlib import Path

# Reuse secrets/env loader from main app
def get_secret(name: str, default: str = ""):
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets.get(name, default)
    except Exception:
        pass
    return os.environ.get(name, default)

from supabase import create_client

SUPABASE_URL = get_secret("SUPABASE_URL", "")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "")
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Apply to LeanChems", page_icon="📌", layout="wide")
st.title("📌 Apply to LeanChems")

# --- DDL (apply in Supabase migrations) ---
# subject_application table
#
# CREATE TABLE IF NOT EXISTS subject_application (
#   id uuid PRIMARY KEY,
#   subject_id uuid REFERENCES subjects(subject_id),
#   input_text text,
#   parsed_data jsonb,
#   coverage_score double precision,
#   scenario_json jsonb,
#   created_at timestamptz DEFAULT now()
# );

@st.cache_data(show_spinner=False)
def get_subjects_dict():
    resp = supabase_client.table('subjects').select('subject_name,subject_id').execute()
    if resp.data:
        return {row['subject_name']: row['subject_id'] for row in resp.data}
    return {}

def run_subject_mapping(subject_id: str, subject_name: str, narrative: str):
    # Placeholder AI processing; integrate your LLM pipeline here.
    # Return parsed structure, coverage score, and scenarios.
    parsed = {
        "layers": [
            {"layer": "Context", "elements": [], "coverage": 0.6},
            {"layer": "Drivers", "elements": [], "coverage": 0.7},
            {"layer": "Metrics", "elements": [], "coverage": 0.9},
            {"layer": "Scenarios", "elements": [], "coverage": 0.8},
        ]
    }
    coverage_score = 85.0
    scenarios = {
        "current": {"summary": f"Current summary for {subject_name}"},
        "next": [
            {"scenario": "Option A", "confidence": 0.7},
            {"scenario": "Option B", "confidence": 0.5},
        ]
    }
    return parsed, coverage_score, scenarios

with st.container():
    subjects = get_subjects_dict()
    if not subjects:
        st.warning("No subjects found. Create one first.")
        st.stop()

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        selected_name = st.selectbox("Select Subject", options=sorted(subjects.keys()))
        narrative = st.text_area("Describe LeanChems situation", height=180)
        uploaded = st.file_uploader("Optional: Upload supporting file (PDF, Excel, etc.)")
        run = st.button("Run Subject Mapping", type="primary")

    with col2:
        if run and selected_name and narrative:
            with st.spinner("Analyzing and mapping to framework..."):
                subject_id = subjects[selected_name]
                parsed, coverage, scenarios = run_subject_mapping(subject_id, selected_name, narrative)

                # Persist application
                rec = {
                    "id": str(uuid.uuid4()),
                    "subject_id": subject_id,
                    "input_text": narrative,
                    "parsed_data": parsed,
                    "coverage_score": coverage,
                    "scenario_json": scenarios,
                    "created_at": datetime.datetime.now().isoformat()
                }
                try:
                    supabase_client.table('subject_application').insert(rec).execute()
                except Exception as e:
                    st.error(f"Failed to save application: {e}")

                st.subheader("✅ Information Extraction Matrix")
                st.json(parsed)
                st.subheader("📊 Coverage Status")
                st.progress(min(max(int(coverage), 0), 100))
                st.write(f"Overall Coverage: {coverage:.1f}%")
                st.subheader("🧭 Scenario Mapping")
                st.json(scenarios)


