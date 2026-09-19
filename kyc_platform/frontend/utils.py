from frontend.config import API_BASE
import plotly.graph_objects as go
import streamlit as st
import requests
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

def api_get(path: str):
    """GET the backend API. Returns parsed JSON or None on error."""
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=15)
        if r.status_code == 200:
            return r.json()
        st.warning(f"API returned {r.status_code} for GET {path}")
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"❌ Cannot reach backend at {API_BASE}. Is the FastAPI server running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_post(path: str, data: dict):
    """POST to the backend API. Returns parsed JSON or None on error."""
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=60)
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"❌ Cannot reach backend at {API_BASE}. Is the FastAPI server running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_delete(path: str):
    """DELETE to the backend API. Returns parsed JSON or None on error."""
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=30)
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"❌ Cannot reach backend at {API_BASE}. Is the FastAPI server running?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# ─── UI helpers ───────────────────────────────────────────────────────────────

def decision_color(decision: str) -> str:
    return {"APPROVE": "🟢", "REVIEW": "🟡", "ESCALATE": "🔴"}.get(decision or "", "⚪")


def risk_gauge(score: float) -> go.Figure:
    """Plotly gauge chart for a risk score 0–100 — dark themed."""
    if score > 75:
        bar_color  = "#ef4444"
        glow_color = "rgba(239,68,68,0.4)"
    elif score > 45:
        bar_color  = "#f59e0b"
        glow_color = "rgba(245,158,11,0.4)"
    else:
        bar_color  = "#10b981"
        glow_color = "rgba(16,185,129,0.4)"

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Overall Risk Score", "font": {"size": 16, "color": "#94a3b8", "family": "Inter"}},
        number={"font": {"size": 48, "color": "#f1f5f9", "family": "Inter"}, "suffix": ""},
        delta={"reference": 50, "increasing": {"color": "#ef4444"}, "decreasing": {"color": "#10b981"},
               "font": {"color": "#94a3b8"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "#334155",
                "tickfont": {"color": "#64748b", "family": "Inter"},
            },
            "bar":     {"color": bar_color, "thickness": 0.75},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   45], "color": "rgba(16,185,129,0.12)"},
                {"range": [45,  75], "color": "rgba(245,158,11,0.12)"},
                {"range": [75, 100], "color": "rgba(239,68,68,0.12)"},
            ],
            "threshold": {
                "line": {"color": "#ef4444", "width": 3},
                "thickness": 0.75,
                "value": 75,
            },
        },
    ))
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#f1f5f9"},
    )
    return fig


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a premium gradient page header."""
    icon_html = f'<span class="page-icon">{icon}</span>' if icon else ""
    sub_html  = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-header-inner">
                {icon_html}
                <div>
                    <h1 class="page-title">{title}</h1>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value, color: str = "#00d4ff", icon: str = ""):
    """Render a glowing KPI metric card."""
    st.markdown(
        f"""
        <div class="kpi-card" style="--kpi-color:{color};">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── Master CSS ───────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── CSS Variables ───────────────────────────────────────────────── */
:root {
    --bg-base:        #0a0e1a;
    --bg-surface:     #0d1b2a;
    --bg-card:        rgba(255,255,255,0.04);
    --bg-card-hover:  rgba(255,255,255,0.07);
    --border:         rgba(255,255,255,0.08);
    --border-strong:  rgba(255,255,255,0.15);

    --cyan:    #00d4ff;
    --purple:  #7c3aed;
    --amber:   #f59e0b;
    --green:   #10b981;
    --red:     #ef4444;
    --blue:    #3b82f6;

    --text-primary: #f1f5f9;
    --text-muted:   #64748b;
    --text-dim:     #94a3b8;

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;

    --shadow-glow-cyan:   0 0 24px rgba(0,212,255,0.18);
    --shadow-glow-purple: 0 0 24px rgba(124,58,237,0.18);
    --shadow-card: 0 8px 32px rgba(0,0,0,0.4);
    --transition: 0.25s ease;
}

/* ── Base Reset ───────────────────────────────────────────────────── */
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

/* Dark color scheme: tells browser to use dark defaults for ALL form controls */
html, body { color-scheme: dark !important; background-color: #0a0e1a !important; }

/* Hide Streamlit's automatic multi-page sidebar navigation */
[data-testid="stSidebarNav"] { display: none !important; }

/* Main app background */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 50%, #0a0f1e 100%) !important;
    background-attachment: fixed !important;
    min-height: 100vh;
}

/* ── Streamlit element overrides ──────────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px !important;
    background: transparent !important;
}
.stApp > div, .stApp header, section.main {
    background: transparent !important;
}

/* Headings */
h1, h2, h3, h4, h5, h6 { color: var(--text-primary) !important; }

/* Text */
p, li, label, span { color: var(--text-dim) !important; }

/* Streamlit native metric widget */
[data-testid="metric-container"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1rem !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--cyan) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* Streamlit tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
    gap: 4px !important;
    padding: 4px !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(0,212,255,0.12) !important;
    color: var(--cyan) !important;
}

/* ── INPUTS: Comprehensive dark theme ───────────────────────────── */

/* 1. Raw HTML input elements */
input, input[type="text"], input[type="number"], input[type="email"],
input[type="password"], input[type="search"],
input:not([type="radio"]):not([type="checkbox"]):not([type="range"]):not([type="file"]) {
    background:       #0f1e30 !important;
    background-color: #0f1e30 !important;
    border:           1px solid rgba(255,255,255,0.15) !important;
    border-radius:    8px !important;
    color:            #f1f5f9 !important;
    caret-color:      #00d4ff !important;
    transition:       border-color 0.2s ease, box-shadow 0.2s ease !important;
}
input:focus, input:not([type="radio"]):not([type="checkbox"]):not([type="range"]):not([type="file"]):focus {
    border-color: #00d4ff !important;
    box-shadow:   0 0 0 2px rgba(0,212,255,0.2) !important;
    outline:      none !important;
}

/* 2. Autofill override — prevents browser from painting white/yellow background */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
    -webkit-box-shadow:      0 0 0 30px #0f1e30 inset !important;
    -webkit-text-fill-color: #f1f5f9 !important;
    caret-color:             #00d4ff !important;
    transition:              background-color 9999s ease-in-out 0s !important;
}

/* 3. Textarea */
textarea {
    background:       #0f1e30 !important;
    background-color: #0f1e30 !important;
    border:           1px solid rgba(255,255,255,0.15) !important;
    border-radius:    8px !important;
    color:            #f1f5f9 !important;
    caret-color:      #00d4ff !important;
}
textarea:focus {
    border-color: #00d4ff !important;
    box-shadow:   0 0 0 2px rgba(0,212,255,0.2) !important;
    outline:      none !important;
}

/* ── SELECTBOX: dark control area ──────────────────────────────── */
/* Control box — cover every depth of baseweb nested divs */
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div,
[data-baseweb="select"] > div > div > div,
[data-baseweb="select"] > div > div > div > div {
    background:       #0f1e30 !important;
    background-color: #0f1e30 !important;
    border-color:     rgba(255,255,255,0.15) !important;
    border-radius:    8px !important;
    color:            #f1f5f9 !important;
}
/* Selected value text and placeholder */
[data-baseweb="select"] span,
[data-baseweb="select"] input {
    color:      #f1f5f9 !important;
    background: transparent !important;
}
/* Dropdown chevron SVG */
[data-baseweb="select"] svg { fill: #64748b !important; }
/* Focus ring on control */
[data-baseweb="select"]:focus-within > div {
    border-color: #00d4ff !important;
    box-shadow:   0 0 0 2px rgba(0,212,255,0.18) !important;
}
/* Streamlit outer wrapper white-bg kill */
[data-testid="stSelectbox"] > div,
[data-testid="stSelectbox"] > div > div { background: transparent !important; }

/* ── DROPDOWN POPUP: Streamlit portals this to body level ──────── */
/* Streamlit renders the open dropdown in: body > div[data-baseweb="layer"] */
body [data-baseweb="layer"],
body [data-baseweb="layer"] > div,
body [data-baseweb="layer"] [data-baseweb="popover"],
body [data-baseweb="layer"] [data-baseweb="menu"],
body [data-baseweb="layer"] ul {
    background:    #0d1b2a !important;
    border:        1px solid rgba(0,212,255,0.2) !important;
    border-radius: 10px !important;
    box-shadow:    0 12px 40px rgba(0,0,0,0.6) !important;
}
body [data-baseweb="layer"] li,
body [data-baseweb="layer"] [role="option"] {
    background: #0d1b2a !important;
    color:      #f1f5f9 !important;
    transition: background 0.15s ease !important;
}
body [data-baseweb="layer"] li:hover,
body [data-baseweb="layer"] [role="option"]:hover,
body [data-baseweb="layer"] [aria-selected="true"] {
    background: rgba(0,212,255,0.12) !important;
    color:      #00d4ff !important;
}

/* ── Number input wrapper ───────────────────────────────────── */
[data-testid="stNumberInput"] > div,
[data-testid="stNumberInputField"],
[data-baseweb="input"],
[data-baseweb="input"] > div {
    background:    #0f1e30 !important;
    border:        1px solid rgba(255,255,255,0.15) !important;
    border-radius: 8px !important;
    color:         #f1f5f9 !important;
}
/* +/- stepper buttons */
[data-baseweb="input"] button {
    background:   rgba(255,255,255,0.06) !important;
    color:        #94a3b8 !important;
    border-color: rgba(255,255,255,0.1) !important;
}
[data-baseweb="input"] button:hover { background: rgba(0,212,255,0.12) !important; color: #00d4ff !important; }

/* ── Streamlit wrapper transparent overrides ─────────────────── */
.stTextInput > div > div,
.stTextArea > div > div,
.stNumberInput > div > div { background: transparent !important; border: none !important; }

/* ── Labels ────────────────────────────────────────────────── */
.stTextInput label, .stTextArea label, .stNumberInput label,
.stSelectbox label, .stFileUploader label, label {
    color:           #94a3b8 !important;
    font-weight:     500 !important;
    font-size:       0.78rem !important;
    text-transform:  uppercase !important;
    letter-spacing:  0.07em !important;
}

/* ── Buttons ──────────────────────────────────────────────── */
/* Default (secondary) button — soft ghost style */
.stButton > button {
    background:    rgba(255,255,255,0.05) !important;
    color:         #94a3b8 !important;
    border:        1px solid rgba(255,255,255,0.14) !important;
    border-radius: var(--radius-sm) !important;
    font-weight:   600 !important;
    font-size:     0.875rem !important;
    letter-spacing:0.04em !important;
    padding:       0.6rem 1.4rem !important;
    transition:    all var(--transition) !important;
    box-shadow:    none !important;
}
.stButton > button p {
    color: inherit !important;
}
.stButton > button:hover {
    background:   rgba(255,255,255,0.09) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color:        #f1f5f9 !important;
    transform:    translateY(-1px) !important;
    box-shadow:   none !important;
}
/* Primary button — keep the full neon gradient for clear CTA hierarchy */
.stButton > button[kind="primary"] {
    background:  linear-gradient(135deg, var(--cyan) 0%, var(--purple) 100%) !important;
    color:       #ffffff !important;
    border:      none !important;
    box-shadow:  0 4px 18px rgba(0,212,255,0.22) !important;
}
.stButton > button[kind="primary"] p {
    color:       #ffffff !important;
    font-weight: 600 !important;
}
.stButton > button[kind="primary"]:hover {
    transform:  translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,212,255,0.38) !important;
    background: linear-gradient(135deg, var(--cyan) 0%, var(--purple) 100%) !important;
    color:      #ffffff !important;
}

/* Form submit button */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, var(--cyan), var(--purple)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.65rem 2rem !important;
    box-shadow: 0 4px 16px rgba(0,212,255,0.25) !important;
    transition: all var(--transition) !important;
}
.stFormSubmitButton > button p {
    color: #ffffff !important;
    font-weight: 600 !important;
}
.stFormSubmitButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(0,212,255,0.4) !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

/* Expander */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(12px) !important;
}
[data-testid="stExpander"] summary { color: var(--text-dim) !important; font-weight: 500 !important; }

/* Info / Warning / Error / Success */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    backdrop-filter: blur(12px) !important;
}
.stAlert[data-baseweb="notification"] { background: rgba(0,212,255,0.06) !important; }

/* Toggle */
[data-testid="stToggle"] { accent-color: var(--cyan) !important; }

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: var(--cyan) !important; }

/* Radio buttons (navigation) */
[data-testid="stSidebar"] [role="radiogroup"] label {
    color: var(--text-dim) !important;
    padding: 0.5rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    transition: all var(--transition) !important;
    font-weight: 500 !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.5rem !important;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(0,212,255,0.08) !important;
    color: var(--cyan) !important;
}
[data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] + div label,
[data-testid="stSidebar"] [data-checked="true"] label {
    background: rgba(0,212,255,0.12) !important;
    color: var(--cyan) !important;
}

/* ── File Uploader ─────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background:    rgba(255,255,255,0.025) !important;
    border:        1px dashed rgba(255,255,255,0.16) !important;
    border-radius: var(--radius-md) !important;
    padding:       1rem !important;
    transition:    border-color var(--transition) !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(0,212,255,0.35) !important;
    background:   rgba(0,212,255,0.03) !important;
}
/* The inner "Browse files" button — override the neon gradient */
[data-testid="stFileUploader"] button,
[data-testid="stFileUploaderDropzone"] button {
    background:    rgba(255,255,255,0.07) !important;
    color:         #94a3b8 !important;
    border:        1px solid rgba(255,255,255,0.14) !important;
    border-radius: 6px !important;
    font-size:     0.8rem !important;
    font-weight:   500 !important;
    box-shadow:    none !important;
    padding:       0.4rem 1rem !important;
}
[data-testid="stFileUploader"] button:hover,
[data-testid="stFileUploaderDropzone"] button:hover {
    background:   rgba(0,212,255,0.1) !important;
    border-color: rgba(0,212,255,0.3) !important;
    color:        #00d4ff !important;
    transform:    none !important;
    box-shadow:   none !important;
}
/* Upload text inside the dropzone */
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] small {
    color: #475569 !important;
    font-size: 0.8rem !important;
}

/* Selectbox dropdown */
[data-baseweb="select"] [data-baseweb="control"] {
    background: rgba(255,255,255,0.04) !important;
    border-color: var(--border-strong) !important;
}
[data-baseweb="select"] [data-baseweb="option"] {
    background: #0d1b2a !important;
    color: var(--text-primary) !important;
}

/* Plotly charts transparent background */
.js-plotly-plot .plotly, .js-plotly-plot .plotly svg { border-radius: var(--radius-md); }

/* ── Sidebar ───────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b2a 0%, #080e1a 100%) !important;
    border-right: 1px solid var(--border) !important;
    max-height: 100vh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
section[data-testid="stSidebar"] > div { max-height: 100vh !important; }
section[data-testid="stSidebar"]::-webkit-scrollbar { width: 4px; }
section[data-testid="stSidebar"]::-webkit-scrollbar-track { background: transparent; }
section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: rgba(0,212,255,0.3);
    border-radius: 4px;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: var(--text-primary) !important; }
section[data-testid="stSidebar"] .stCaption { font-size: 11px; color: var(--text-muted) !important; }

/* ── Custom Component Styles ──────────────────────────────────────── */

/* Page Header */
.page-header {
    background: linear-gradient(135deg, rgba(0,212,255,0.06) 0%, rgba(124,58,237,0.06) 100%);
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: var(--radius-lg);
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.page-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--cyan), transparent);
}
.page-header-inner { display: flex; align-items: center; gap: 1rem; }
.page-icon { font-size: 2.2rem; line-height: 1; }
.page-title {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, var(--cyan), var(--purple));
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    margin: 0 !important;
    padding: 0 !important;
}
.page-subtitle { color: var(--text-muted) !important; font-size: 0.875rem !important; margin: 0.25rem 0 0 0 !important; }

/* KPI Card */
.kpi-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.25rem 1rem;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: all var(--transition);
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: var(--kpi-color, var(--cyan));
    opacity: 0.8;
}
.kpi-card:hover {
    border-color: var(--kpi-color, var(--cyan));
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    transform: translateY(-2px);
}
.kpi-icon { font-size: 1.6rem; margin-bottom: 0.4rem; }
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--kpi-color, var(--cyan)) !important;
    line-height: 1.1;
    -webkit-text-fill-color: var(--kpi-color, var(--cyan)) !important;
}
.kpi-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted) !important;
    margin-top: 0.3rem;
    font-weight: 500;
}

/* Decision Banner */
.decision-approve {
    background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.06));
    border: 1px solid rgba(16,185,129,0.35);
    border-left: 4px solid var(--green);
    padding: 1.25rem 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 24px rgba(16,185,129,0.1), inset 0 1px 0 rgba(16,185,129,0.1);
}
.decision-review {
    background: linear-gradient(135deg, rgba(245,158,11,0.12), rgba(245,158,11,0.06));
    border: 1px solid rgba(245,158,11,0.35);
    border-left: 4px solid var(--amber);
    padding: 1.25rem 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 24px rgba(245,158,11,0.1), inset 0 1px 0 rgba(245,158,11,0.1);
}
.decision-escalate {
    background: linear-gradient(135deg, rgba(239,68,68,0.12), rgba(239,68,68,0.06));
    border: 1px solid rgba(239,68,68,0.35);
    border-left: 4px solid var(--red);
    padding: 1.25rem 1.5rem;
    border-radius: var(--radius-md);
    box-shadow: 0 4px 24px rgba(239,68,68,0.1), inset 0 1px 0 rgba(239,68,68,0.1);
}
.decision-approve h2, .decision-approve h3,
.decision-approve p, .decision-approve b { color: #a7f3d0 !important; }
.decision-review h2, .decision-review h3,
.decision-review p, .decision-review b { color: #fde68a !important; }
.decision-escalate h2, .decision-escalate h3,
.decision-escalate p, .decision-escalate b { color: #fca5a5 !important; }

/* Agent Pipeline Card */
.agent-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.85rem 1.25rem;
    margin: 0.35rem 0;
    transition: all var(--transition);
    position: relative;
    overflow: hidden;
}
.agent-card:hover { border-color: var(--border-strong); background: var(--bg-card-hover); }
.agent-card-done {
    border-color: rgba(16,185,129,0.3) !important;
    background: rgba(16,185,129,0.04) !important;
}
.agent-card-done::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: var(--green);
    border-radius: 3px 0 0 3px;
}
.agent-card-active {
    border-color: rgba(245,158,11,0.5) !important;
    background: rgba(245,158,11,0.06) !important;
    box-shadow: 0 0 20px rgba(245,158,11,0.1) !important;
    animation: pulse-amber 2s infinite;
}
.agent-card-active::before {
    content: '';
    position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
    background: var(--amber);
    border-radius: 3px 0 0 3px;
}
.agent-card-waiting {
    border-color: var(--border) !important;
    opacity: 0.5;
}
@keyframes pulse-amber {
    0%, 100% { box-shadow: 0 0 12px rgba(245,158,11,0.1); }
    50%       { box-shadow: 0 0 28px rgba(245,158,11,0.25); }
}
@keyframes pulse-green {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.6; }
}

/* Status dot */
.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.status-dot-done    { background: var(--green); box-shadow: 0 0 8px rgba(16,185,129,0.6); }
.status-dot-active  { background: var(--amber); box-shadow: 0 0 8px rgba(245,158,11,0.6); animation: pulse-green 1.5s infinite; }
.status-dot-waiting { background: #334155; }

/* Risk Flag Badge */
.flag-badge {
    background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.1));
    border: 1px solid rgba(239,68,68,0.4);
    color: #fca5a5 !important;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    margin: 3px 2px;
    display: inline-block;
    font-weight: 600;
    letter-spacing: 0.04em;
    -webkit-text-fill-color: #fca5a5 !important;
}

/* Evidence Trail Card */
.evidence-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin: 0.5rem 0;
    transition: all var(--transition);
}
.evidence-card:hover { border-color: var(--border-strong); }
.evidence-neg { border-left: 3px solid var(--red) !important; }
.evidence-pos { border-left: 3px solid var(--green) !important; }
.evidence-neu { border-left: 3px solid var(--text-muted) !important; }

/* Step Progress Indicator */
.step-progress {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 1.5rem 0;
    padding: 1rem;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
}
.step-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    flex: 1;
    position: relative;
}
.step-item:not(:last-child)::after {
    content: '';
    position: absolute;
    top: 18px;
    left: 60%;
    right: -40%;
    height: 2px;
    background: var(--border-strong);
    z-index: 0;
}
.step-item.active:not(:last-child)::after,
.step-item.done:not(:last-child)::after {
    background: linear-gradient(90deg, var(--cyan), var(--border-strong));
}
.step-circle {
    width: 36px; height: 36px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    z-index: 1;
    position: relative;
    border: 2px solid var(--border-strong);
    background: var(--bg-surface);
    color: var(--text-muted);
}
.step-item.done .step-circle {
    background: rgba(16,185,129,0.15);
    border-color: var(--green);
    color: var(--green);
}
.step-item.active .step-circle {
    background: rgba(0,212,255,0.15);
    border-color: var(--cyan);
    color: var(--cyan);
    box-shadow: 0 0 16px rgba(0,212,255,0.4);
}
.step-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted) !important;
    font-weight: 500;
    text-align: center;
}
.step-item.active .step-label { color: var(--cyan) !important; }
.step-item.done .step-label { color: var(--green) !important; }

/* Sidebar Logo Area */
.sidebar-logo {
    background: linear-gradient(135deg, rgba(0,212,255,0.08), rgba(124,58,237,0.08));
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: var(--radius-md);
    padding: 1rem 1.25rem;
    margin-bottom: 0.5rem;
    text-align: center;
}
.sidebar-logo-title {
    font-size: 1.1rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--cyan), var(--purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.sidebar-logo-sub {
    font-size: 0.65rem;
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.15rem;
}

/* Hackathon badge */
.hackathon-badge {
    background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(0,212,255,0.08));
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: var(--radius-sm);
    padding: 0.6rem 0.9rem;
    font-size: 0.7rem;
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    margin-top: 0.5rem;
}
.hackathon-badge b {
    color: #c4b5fd !important;
    -webkit-text-fill-color: #c4b5fd !important;
}

/* Threshold legend */
.threshold-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0;
    font-size: 0.72rem;
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
}
.threshold-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* Audit event card */
.audit-event {
    background: var(--bg-card);
    border-radius: var(--radius-sm);
    padding: 0.65rem 1rem;
    margin: 0.3rem 0;
    border-left: 3px solid var(--border-strong);
    transition: all var(--transition);
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}
.audit-event:hover { background: var(--bg-card-hover); }
.audit-event-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;
}
.audit-event code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important;
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
    background: transparent !important;
}

/* Form container */
.form-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    backdrop-filter: blur(12px);
}

/* Glowing section divider */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-strong), transparent);
    margin: 1.5rem 0;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.2); border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,212,255,0.4); }
</style>
"""
