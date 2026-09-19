import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
import plotly.express as px
import pandas as pd

from frontend.utils import api_get, decision_color, page_header, risk_gauge

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "Inter", "color": "#94a3b8"},
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
)


def _render_json_beautifully(data_dict):
    """Renders dictionaries as beautiful HTML grids or error cards instead of raw JSON."""
    if not data_dict:
        st.markdown('<div style="color:#64748b;font-size:0.85rem;padding:1rem;">No data available.</div>', unsafe_allow_html=True)
        return
    
    if "error" in data_dict:
        err  = data_dict.get("error", "Error")
        det  = data_dict.get("details", "")
        conf = data_dict.get("confidence", "")
        st.markdown(f'''
            <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); border-radius:10px; padding:1.5rem; margin-top:0.5rem;">
                <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.5rem;">
                    <span style="font-size:1.5rem;">❌</span>
                    <span style="color:#fca5a5; font-weight:700; font-size:1.1rem; text-transform:uppercase;">{err}</span>
                </div>
                <div style="color:#fecaca; font-size:0.9rem; margin-bottom:1rem;">{det}</div>
                <span style="background:rgba(239,68,68,0.2); color:#f87171; padding:0.2rem 0.6rem; border-radius:4px; font-size:0.75rem; font-weight:600; letter-spacing:0.05em;">CONFIDENCE: {conf}</span>
            </div>
        ''', unsafe_allow_html=True)
        return
    
    html = '<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:1rem; margin-top:0.5rem; display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:1rem;">'
    for k, v in data_dict.items():
        v_str = str(v)
        html += f'''<div>
<div style="font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em; color:#64748b; margin-bottom:0.2rem;">{k.replace("_", " ")}</div>
<div style="font-size:0.85rem; color:#e2e8f0; font-family:'JetBrains Mono', monospace; word-break:break-word;">{v_str}</div>
</div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def _render_agent_logs(logs):
    """Renders agent execution logs as a styled list."""
    if not logs:
        st.markdown('<div style="color:#64748b;font-size:0.85rem;padding:1rem;">No logs available.</div>', unsafe_allow_html=True)
        return
    
    html = '<div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">'
    for log in logs:
        status = str(log.get("status", "unknown")).upper()
        if status == "COMPLETED": color = "#10b981"
        elif status == "ERROR":   color = "#ef4444"
        else:                     color = "#f59e0b"
        
        html += f'''<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:0.8rem 1rem; display:flex; justify-content:space-between; align-items:center;">
<div>
<div style="font-size:0.85rem; font-weight:600; color:#e2e8f0; margin-bottom:0.2rem;">{log.get("agent", "Unknown Agent")}</div>
<div style="font-size:0.7rem; color:#64748b; font-family:'JetBrains Mono', monospace;">{log.get("timestamp", "")}</div>
</div>
<div style="text-align:right;">
<div style="font-size:0.75rem; font-weight:800; color:{color}; letter-spacing:0.05em; margin-bottom:0.2rem;">{status}</div>
<div style="font-size:0.7rem; color:#94a3b8;">{log.get("duration_ms", "0")} ms &nbsp;|&nbsp; Conf: {log.get("confidence", "N/A")}</div>
</div>
</div>'''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)



def render():
    page_header(
        title="Risk Score Dashboard",
        subtitle="Full explainable risk breakdown with agent evidence trail",
        icon="📊",
    )

    customer_id = st.text_input(
        "Customer ID",
        value=st.session_state.get("active_customer_id", ""),
        placeholder="e.g. KYC-GREEN-001",
    )

    if not customer_id.strip():
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#334155;">'
            '<div style="font-size:3rem;margin-bottom:1rem;">📊</div>'
            '<p style="font-size:1rem;color:#475569;">Enter a Customer ID above to view the risk report.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    report = api_get(f"/kyc/report/{customer_id.strip()}")

    if report is None:
        st.error(f"No case found for **{customer_id}**.")
        return

    if not report.get("decision"):
        st.info("Pipeline still processing — check the **⚡ Live Pipeline** page.")
        return

    decision = report["decision"]
    score    = float(report.get("overall_risk_score") or 0)
    band     = report.get("risk_band") or "—"

    # ── Top row: gauge + decision card ───────────────────────────────────────
    g_col, d_col = st.columns([1, 1])
    with g_col:
        st.plotly_chart(risk_gauge(score), use_container_width=True)

    with d_col:
        dec_class = {
            "APPROVE":  "decision-approve",
            "REVIEW":   "decision-review",
            "ESCALATE": "decision-escalate",
        }.get(decision, "")
        dec_icon  = decision_color(decision)
        rationale = report.get("decision_rationale", "—")
        st.markdown(
            f'<div class="{dec_class}" style="margin-top:30px;">'
            f'<h2>{dec_icon} {decision}</h2>'
            f'<p><b>Risk Band:</b> {band}&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'<b>Score:</b> {score}/100</p></div>',
            unsafe_allow_html=True,
        )
    # ── Risk flags ────────────────────────────────────────────────────────────
    flags = report.get("flags") or []
    if flags:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.1em;margin:0 0 0.75rem;">🚩 Risk Flags</h3>',
            unsafe_allow_html=True,
        )
        badges = " ".join(f'<span class="flag-badge">{f}</span>' for f in flags)
        st.markdown(badges, unsafe_allow_html=True)

    # ── Evidence trail ────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;margin:0 0 0.75rem;">🔍 Evidence Trail (per agent)</h3>',
        unsafe_allow_html=True,
    )
    for ev in report.get("evidence_trail") or []:
        impact      = ev.get("impact", "NEUTRAL")
        impact_icon = {"NEGATIVE": "🔴", "POSITIVE": "🟢", "NEUTRAL": "⚪"}.get(impact, "⚪")
        ev_class    = {"NEGATIVE": "evidence-neg", "POSITIVE": "evidence-pos", "NEUTRAL": "evidence-neu"}.get(impact, "evidence-neu")
        weight      = int(float(ev.get("weight", 0)) * 100)
        c_score     = ev.get("component_score", "N/A")
        label = (
            f"{impact_icon} **{ev['agent']}** — "
            f"weight: {weight}% | component score: {c_score}"
        )
        with st.expander(label, expanded=(impact == "NEGATIVE")):
            st.markdown(
                f'<div class="evidence-card {ev_class}">'
                f'<p style="color:#cbd5e1;margin:0;">{ev.get("finding", "No details available.")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Recommended actions ───────────────────────────────────────────────────
    actions = report.get("recommended_actions") or []
    if actions:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.1em;margin:0 0 0.75rem;">📋 Recommended Actions</h3>',
            unsafe_allow_html=True,
        )
        for i, action in enumerate(actions, 1):
            st.markdown(
                f'<div style="display:flex;gap:0.75rem;align-items:flex-start;margin:0.4rem 0;">'
                f'<span style="background:rgba(0,212,255,0.12);color:#00d4ff;border-radius:50%;'
                f'width:22px;height:22px;display:flex;align-items:center;justify-content:center;'
                f'font-size:0.7rem;font-weight:700;flex-shrink:0;">{i}</span>'
                f'<span style="color:#cbd5e1;font-size:0.875rem;">{action}</span></div>',
                unsafe_allow_html=True,
            )

    # ── Agent confidence bar chart ────────────────────────────────────────────
    conf = report.get("confidence_scores") or {}
    if conf:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.1em;margin:0 0 0.75rem;">🤖 Agent Confidence Scores</h3>',
            unsafe_allow_html=True,
        )
        df = pd.DataFrame({
            "Agent":      list(conf.keys()),
            "Confidence": [round(v * 100, 1) for v in conf.values()],
        })
        fig = px.bar(
            df, x="Agent", y="Confidence",
            text="Confidence",
            color="Confidence",
            color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
            range_y=[0, 100],
            labels={"Confidence": "Confidence (%)"},
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                          marker_line_width=0)
        fig.update_layout(
            height=350,
            showlegend=False,
            coloraxis_showscale=False,
            **_DARK_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Raw agent logs ────────────────────────────────────────────────────────
    with st.expander("🗒️ Agent Execution Logs"):
        _render_agent_logs(report.get("agent_logs") or [])

    # ── Full report raw view ──────────────────────────────────────────────────
    with st.expander("📄 Full Extraction & Screening Results"):
        tabs = st.tabs(["Extraction", "Enrichment", "Verification", "Screening", "Financial"])
        with tabs[0]: _render_json_beautifully(report.get("extraction_result")   or {})
        with tabs[1]: _render_json_beautifully(report.get("enrichment_result")   or {})
        with tabs[2]: _render_json_beautifully(report.get("verification_result") or {})
        with tabs[3]: _render_json_beautifully(report.get("screening_result")    or {})
        with tabs[4]: _render_json_beautifully(report.get("financial_profile")   or {})


# force reload
