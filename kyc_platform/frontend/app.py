"""
DN Agentic KYC Intelligence Platform — Streamlit Frontend
Run: cd kyc_platform && python run_frontend.py
"""

from frontend.pages import onboarding, live_pipeline, risk_dashboard, human_review, audit_log, global_metrics
from frontend.utils import CUSTOM_CSS
import streamlit as st
import sys
import os

# ── Path bootstrap (required for Streamlit: runs as __main__, not a module) ──
# .../kyc_platform/frontend
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)                              # .../kyc_platform
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


st.set_page_config(
    page_title="DN KYC Intelligence Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Sidebar Navigation ────────────────────────────────────────────────────────
st.sidebar.markdown(
    """
    <div class="sidebar-logo">
        <div class="sidebar-logo-title">🏦 DN KYC Platform</div>
        <div class="sidebar-logo-sub">Agentic Intelligence System</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div class="hackathon-badge">
        <b>⚡ AMD ROCm</b> &nbsp;·&nbsp; <b>vLLM</b> &nbsp;·&nbsp; <b>LangGraph</b><br>
        <b>FastAPI</b> &nbsp;·&nbsp; <b>Python</b>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()
st.sidebar.markdown(
    '<p style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:#475569;font-weight:600;margin-bottom:0.5rem;">Navigation</p>',
    unsafe_allow_html=True,
)

PAGES = {
    "🧾 Customer Onboarding": onboarding,
    "⚡ Live Pipeline":       live_pipeline,
    "📊 Risk Dashboard":      risk_dashboard,
    "👤 Human Review Queue":  human_review,
    "📋 Audit Log":           audit_log,
    "📈 Global Metrics":      global_metrics,
}

current_nav = st.session_state.get("nav", "🧾 Customer Onboarding")
options_list = list(PAGES.keys())
try:
    nav_index = options_list.index(current_nav)
except ValueError:
    nav_index = 0

page_name = st.sidebar.radio(
    label="nav",
    options=options_list,
    index=nav_index,
    label_visibility="collapsed",
    key="nav_radio"
)
st.session_state["nav"] = page_name

st.sidebar.divider()

st.sidebar.markdown(
    """
    <div style="padding:0.25rem 0;">
        <p style="font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:#475569;font-weight:600;margin-bottom:0.75rem;">Decision Thresholds</p>
        <div class="threshold-item"><div class="threshold-dot" style="background:#10b981;box-shadow:0 0 6px rgba(16,185,129,0.6);"></div> Score &lt; 45 → <b style="color:#a7f3d0;-webkit-text-fill-color:#a7f3d0;">APPROVE</b></div>
        <div class="threshold-item"><div class="threshold-dot" style="background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,0.6);"></div> Score 45–75 → <b style="color:#fde68a;-webkit-text-fill-color:#fde68a;">REVIEW</b></div>
        <div class="threshold-item"><div class="threshold-dot" style="background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,0.6);"></div> Score &gt; 75 → <b style="color:#fca5a5;-webkit-text-fill-color:#fca5a5;">ESCALATE</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div class="hackathon-badge" style="text-align:center;">
        <div style="font-size:1rem;margin-bottom:0.3rem;">🏆</div>
        <b>TCS × AMD Hackathon 2026</b><br>
        <span style="font-size:0.65rem;color:#64748b;-webkit-text-fill-color:#64748b;">Built on AMD Cloud · Python</span>
    </div>
    """,
    unsafe_allow_html=True,
)

PAGES[page_name].render()
