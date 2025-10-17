import os
import json
import uuid
import datetime
import streamlit as st
from pathlib import Path
from supabase import create_client

def get_secret(name: str, default: str = ""):
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets.get(name, default)
    except Exception:
        pass
    return os.environ.get(name, default)

SUPABASE_URL = get_secret("SUPABASE_URL", "")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "")
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="AI Coach", page_icon="🧠", layout="wide")
st.title("🧠 AI Coach for LeanChems")

# --- DDL (apply in Supabase migrations) ---
# subject_coach_analysis table
#
# CREATE TABLE IF NOT EXISTS subject_coach_analysis (
#   id uuid PRIMARY KEY,
#   subject_application_id uuid REFERENCES subject_application(id),
#   criticality_score double precision,
#   maturity_level text,
#   action_plan_json jsonb,
#   recommendations_text text,
#   created_at timestamptz DEFAULT now()
# );

@st.cache_data(show_spinner=False)
def get_subjects_dict():
    resp = supabase_client.table('subjects').select('subject_name,subject_id').execute()
    if resp.data:
        return {row['subject_name']: row['subject_id'] for row in resp.data}
    return {}

def get_applications(subject_id: str):
    resp = supabase_client.table('subject_application').select('id, created_at, coverage_score').eq('subject_id', subject_id).order('created_at', desc=True).execute()
    return resp.data or []

def run_coach_analysis(subject_name: str, application_row: dict):
    # Placeholder AI; integrate your LLM logic
    criticality = 72.0
    maturity = "Emerging"
    action_plan = {
        "short_term": ["Validate metrics", "Close top gaps"],
        "mid_term": ["Pilot scenario A", "Build dashboards"],
        "long_term": ["Institutionalize process", "Scale to other units"]
    }
    recommendations = f"For {subject_name}, focus on closing gaps with highest impact/urgency."
    return criticality, maturity, action_plan, recommendations

subjects = get_subjects_dict()
if not subjects:
    st.warning("No subjects found. Create one first.")
    st.stop()

col1, col2 = st.columns([0.4, 0.6])
with col1:
    selected_name = st.selectbox("Select Subject", options=sorted(subjects.keys()))
    selected_apps = []
    selected_app_id = None
    if selected_name:
        selected_subject_id = subjects[selected_name]
        selected_apps = get_applications(selected_subject_id)
        app_options = [f"{a['id']} | {a['created_at']} | {a.get('coverage_score', 'n/a')}%" for a in selected_apps]
        chosen = st.selectbox("Select Previous Application", options=app_options if app_options else ["None"])
        if app_options:
            idx = app_options.index(chosen)
            selected_app_id = selected_apps[idx]['id']
    run = st.button("Analyze & Coach", type="primary")

with col2:
    if run and selected_app_id:
        row = next((a for a in selected_apps if a['id'] == selected_app_id), None)
        if not row:
            st.error("Application not found")
        else:
            with st.spinner("Generating strategy and action plan..."):
                criticality, maturity, action_plan, recommendations = run_coach_analysis(selected_name, row)

                rec = {
                    "id": str(uuid.uuid4()),
                    "subject_application_id": selected_app_id,
                    "criticality_score": criticality,
                    "maturity_level": maturity,
                    "action_plan_json": action_plan,
                    "recommendations_text": recommendations,
                    "created_at": datetime.datetime.now().isoformat()
                }
                try:
                    supabase_client.table('subject_coach_analysis').insert(rec).execute()
                except Exception as e:
                    st.error(f"Failed to save coach analysis: {e}")

                st.subheader("📈 Maturity & Criticality")
                st.metric("Criticality", f"{criticality:.1f}")
                st.write(f"Maturity: {maturity}")
                st.subheader("🧭 Recommended Strategy")
                st.json(action_plan)
                st.subheader("📝 Narrative Recommendations")
                st.write(recommendations)


