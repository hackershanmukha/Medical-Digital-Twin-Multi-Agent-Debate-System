"""
Medical AI Clinical Decision Support System
Streamlit Demo App — Main Entry Point
"""
import sys
import os

# ── Path setup so we can import from project root ──────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import streamlit as st

# ── Page config must be called before any other st.* commands ──────────────
st.set_page_config(
    page_title="MedTwin AI — Clinical Decision Support",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 50%, #0d1b2a 100%);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2 { color: #7dd3fc !important; }

/* Main content */
.main .block-container { padding-top: 1.5rem; }
.stApp { background: #f8fafc; }

/* Cards */
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

/* Risk badges */
.risk-low    { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.risk-moderate { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
.risk-high   { background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5; }
.risk-very-high { background: #fce7f3; color: #9d174d; border: 1px solid #f9a8d4; }
.risk-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Agent cards in debate */
.agent-card {
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid;
}
.agent-cardiology   { border-color: #ef4444; background: #fff5f5; }
.agent-endocrinology { border-color: #8b5cf6; background: #faf5ff; }
.agent-gp           { border-color: #3b82f6; background: #eff6ff; }
.agent-moderator    { border-color: #f59e0b; background: #fffbeb; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: white;
    border-radius: 12px;
    padding: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 500;
}

/* Buttons */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s;
}
.stButton > button:hover { transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)


# ── Session state ────────────────────────────────────────────────────────────
if "patient_twin" not in st.session_state:
    st.session_state.patient_twin = None
if "risk_results" not in st.session_state:
    st.session_state.risk_results = None
if "debate_result" not in st.session_state:
    st.session_state.debate_result = None
if "page" not in st.session_state:
    st.session_state.page = "home"


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧬 MedTwin AI")
    st.markdown("*Clinical Decision Support System*")
    st.divider()

    st.markdown("### Navigation")
    pages = {
        "🏠 Home": "home",
        "👤 Patient Profile": "patient",
        "📊 Risk Analysis": "risk",
        "🗣️ Clinical Debate": "debate",
        "📋 Consensus Report": "report",
    }
    for label, key in pages.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state.page = key

    st.divider()

    # Status indicators
    st.markdown("### System Status")
    twin_ok = st.session_state.patient_twin is not None
    risk_ok = st.session_state.risk_results is not None
    debate_ok = st.session_state.debate_result is not None

    st.markdown(f"{'✅' if twin_ok else '⏳'} Patient Profile")
    st.markdown(f"{'✅' if risk_ok else '⏳'} Risk Analysis")
    st.markdown(f"{'✅' if debate_ok else '⏳'} Debate Complete")

    st.divider()
    st.markdown(
        "<small>Built for Kaggle Hackathon 2026<br>"
        "Powered by Gemini 2.5 Pro + XGBoost</small>",
        unsafe_allow_html=True,
    )


# ── Page routing ─────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    from streamlit_app.pages import home
    home.render()
elif page == "patient":
    from streamlit_app.pages import patient_profile
    patient_profile.render()
elif page == "risk":
    from streamlit_app.pages import risk_analysis
    risk_analysis.render()
elif page == "debate":
    from streamlit_app.pages import debate_view
    debate_view.render()
elif page == "report":
    from streamlit_app.pages import consensus_report
    consensus_report.render()
