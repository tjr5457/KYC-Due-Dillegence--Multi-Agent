from frontend.utils import api_get, page_header
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cbd5e1"),
    margin=dict(l=20, r=20, t=40, b=20),
)


def render():
    page_header(
        title="Global Metrics",
        subtitle="High-level business ROI and automation statistics",
        icon="📈",
    )

    all_cases_data = api_get("/kyc/cases") or {"cases": []}
    all_cases = all_cases_data.get("cases", [])

    if not all_cases:
        st.info("No cases have been processed yet.")
        return

    # Compute metrics
    total_cases = len(all_cases)
    auto_approved = len([c for c in all_cases if c.get(
        "final_decision") == "APPROVE" and not c.get("human_decision")])
    requires_human = len(
        [c for c in all_cases if c.get("human_review_required")])
    human_reviewed = len([c for c in all_cases if c.get("human_decision")])
    escalated = len([c for c in all_cases if c.get(
        "final_decision") == "ESCALATE" and not c.get("human_decision")])

    automation_rate = (auto_approved / total_cases *
                       100) if total_cases > 0 else 0

    # ── KPI Row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#38bdf8;">'
            f'<div class="kpi-icon">📈</div>'
            f'<div class="kpi-value">{total_cases}</div>'
            f'<div class="kpi-label">Total Cases</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#10b981;">'
            f'<div class="kpi-icon">🤖</div>'
            f'<div class="kpi-value">{automation_rate:.1f}%</div>'
            f'<div class="kpi-label">Automation Rate</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#f59e0b;">'
            f'<div class="kpi-icon">👤</div>'
            f'<div class="kpi-value">{requires_human}</div>'
            f'<div class="kpi-label">Human Review Needed</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#8b5cf6;">'
            f'<div class="kpi-icon">✅</div>'
            f'<div class="kpi-value">{human_reviewed}</div>'
            f'<div class="kpi-label">Analyst Resolutions</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts Row ────────────────────────────────────────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            '<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1rem;">'
            '<h3 style="font-size:0.9rem;color:#94a3b8;margin-top:0;">AI Decision Distribution</h3>',
            unsafe_allow_html=True,
        )
        decisions = [c.get("final_decision", "PENDING") for c in all_cases]
        df_dec = pd.Series(decisions).value_counts().reset_index()
        df_dec.columns = ["Decision", "Count"]

        color_map = {"APPROVE": "#10b981", "REVIEW": "#f59e0b",
                     "ESCALATE": "#ef4444", "PENDING": "#64748b"}
        fig_pie = px.pie(df_dec, values="Count", names="Decision",
                         hole=0.6, color="Decision", color_discrete_map=color_map)
        fig_pie.update_layout(height=300, **_DARK_LAYOUT)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(
            '<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1rem;">'
            '<h3 style="font-size:0.9rem;color:#94a3b8;margin-top:0;">Analyst Activity Funnel</h3>',
            unsafe_allow_html=True,
        )

        funnel_data = dict(
            stage=["Total Cases", "Requires Review", "Reviewed by Analyst"],
            value=[total_cases, requires_human, human_reviewed]
        )
        fig_funnel = px.funnel(funnel_data, x='value', y='stage')
        fig_funnel.update_layout(height=300, **_DARK_LAYOUT)
        fig_funnel.update_traces(marker=dict(
            color=["#38bdf8", "#f59e0b", "#10b981"]))
        st.plotly_chart(fig_funnel, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
