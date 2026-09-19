import sys
import os
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from frontend.utils import api_get, decision_color, page_header

# Ordered agent list for the pipeline diagram
PIPELINE_AGENTS = [
    ("DataExtractorAgent",       "🔍", "Extract & parse identity fields"),
    ("EnrichmentAgent",          "🔗", "Cross-reference & enrich profile"),
    ("IDVerificationAgent",      "🪪", "Verify document authenticity"),
    ("ComplianceScreeningAgent", "🛡️", "Sanctions · PEP · Watchlist"),
    ("FinancialProfileAgent",    "💰", "Financial risk profiling"),
    ("DecisionNode",             "⚖️",  "Risk scoring & final decision"),
]


def _agent_card(agent_name, icon, description, logs, current_agent, final_decision):
    """Render one premium agent row with animated status."""
    done       = any(l["agent"] == agent_name for l in logs)
    if agent_name == "DecisionNode" and final_decision:
        done = True
    is_current = (current_agent == agent_name) and not final_decision

    if done:
        card_class  = "agent-card agent-card-done"
        dot_class   = "status-dot status-dot-done"
        status_text = '<span style="color:#10b981;font-weight:600;font-size:0.75rem;">COMPLETED</span>'
    elif is_current:
        card_class  = "agent-card agent-card-active"
        dot_class   = "status-dot status-dot-active"
        status_text = '<span style="color:#f59e0b;font-weight:600;font-size:0.75rem;">RUNNING…</span>'
    else:
        card_class  = "agent-card agent-card-waiting"
        dot_class   = "status-dot status-dot-waiting"
        status_text = '<span style="color:#334155;font-weight:600;font-size:0.75rem;">PENDING</span>'

    detail_html = ""
    if done:
        if agent_name == "DecisionNode":
            detail_html = (
                f'<div style="display:flex;gap:1rem;margin-top:0.4rem;flex-wrap:wrap;">'
                f'<span style="font-size:0.7rem;color:#475569;">⏱ — ms</span>'
                f'<span style="font-size:0.7rem;color:#475569;">🎯 Conf: HIGH</span></div>'
            )
        else:
            log = next(l for l in logs if l["agent"] == agent_name)
            dur  = log.get("duration_ms", "—")
            conf = log.get("confidence", "—")
            detail_html = (
                f'<div style="display:flex;gap:1rem;margin-top:0.4rem;flex-wrap:wrap;">'
                f'<span style="font-size:0.7rem;color:#475569;">⏱ {dur} ms</span>'
                f'<span style="font-size:0.7rem;color:#475569;">🎯 Conf: {conf}</span>'
            )
            if log.get("flags_raised"):
                for f in log["flags_raised"]:
                    detail_html += f'<span class="flag-badge">{f}</span>'
            detail_html += "</div>"
    elif is_current:
        detail_html = '<div style="margin-top:0.3rem;font-size:0.72rem;color:#92400e;font-style:italic;">Processing…</div>'

    st.markdown(
        f'<div class="{card_class}">'
        f'<div class="{dot_class}"></div>'
        f'<div style="font-size:1.4rem;min-width:2rem;">{icon}</div>'
        f'<div style="flex:1;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<span style="font-weight:600;color:#f1f5f9;font-size:0.9rem;">{agent_name}</span>'
        f'{status_text}'
        f'</div>'
        f'<div style="font-size:0.75rem;color:#64748b;margin-top:0.1rem;">{description}</div>{detail_html}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def render():
    page_header(
        title="Live Agent Pipeline",
        subtitle="Watch each KYC agent execute step-by-step in real time",
        icon="⚡",
    )

    col_id, col_toggle = st.columns([3, 1])
    with col_id:
        customer_id = st.text_input(
            "Customer ID to monitor",
            value=st.session_state.get("active_customer_id", ""),
            placeholder="e.g. KYC-GREEN-001",
        )
    with col_toggle:
        st.markdown("<br>", unsafe_allow_html=True)
        auto_refresh = st.toggle("Auto-refresh (4s)", value=True)

    if not customer_id.strip():
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#334155;">'
            '<div style="font-size:3rem;margin-bottom:1rem;">⚡</div>'
            '<p style="font-size:1rem;color:#475569;">Enter a Customer ID above, or submit a case on the Onboarding page.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    status_data = api_get(f"/kyc/status/{customer_id.strip()}")
    report_data = api_get(f"/kyc/report/{customer_id.strip()}")

    if status_data is None:
        st.error(f"No case found for **{customer_id}**. Check the Customer ID or submit a new case.")
        return

    final_decision = status_data.get("final_decision")
    current_agent  = status_data.get("current_agent") or ""
    logs           = (report_data or {}).get("agent_logs", [])

    # ── Summary KPI Row ───────────────────────────────────────────────────────
    st.markdown(
        f'<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:0.1em;margin:1rem 0 0.5rem;">Case: {customer_id}</h3>',
        unsafe_allow_html=True,
    )

    risk_score = status_data.get("overall_risk_score")
    risk_band  = status_data.get("risk_band", "—")
    agent_cnt  = status_data.get("agent_count", 0)
    fd_display = final_decision or "Processing…"

    kpi_color = {"APPROVE": "#10b981", "REVIEW": "#f59e0b", "ESCALATE": "#ef4444"}.get(
        final_decision, "#00d4ff"
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:{kpi_color};">'
            f'<div class="kpi-icon">⚖️</div>'
            f'<div class="kpi-value" style="font-size:1.1rem;">{fd_display}</div>'
            f'<div class="kpi-label">Status</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#7c3aed;">'
            f'<div class="kpi-icon">📊</div>'
            f'<div class="kpi-value">{risk_score if risk_score is not None else "—"}</div>'
            f'<div class="kpi-label">Risk Score</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#f59e0b;">'
            f'<div class="kpi-icon">🎚️</div>'
            f'<div class="kpi-value" style="font-size:1.2rem;">{risk_band}</div>'
            f'<div class="kpi-label">Risk Band</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#10b981;">'
            f'<div class="kpi-icon">🤖</div>'
            f'<div class="kpi-value">{agent_cnt}</div>'
            f'<div class="kpi-label">Agents Done</div></div>',
            unsafe_allow_html=True,
        )

    # ── Agent pipeline diagram ────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider"></div>'
        '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;margin:1rem 0 0.75rem;">Pipeline Execution</h3>',
        unsafe_allow_html=True,
    )
    for name, icon, desc in PIPELINE_AGENTS:
        _agent_card(name, icon, desc, logs, current_agent, final_decision)

    # ── Risk flags ────────────────────────────────────────────────────────────
    flags = status_data.get("risk_flags", [])
    if flags:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.1em;margin:0 0 0.75rem;">🚩 Risk Flags Raised</h3>',
            unsafe_allow_html=True,
        )
        badges = " ".join(f'<span class="flag-badge">{f}</span>' for f in flags)
        st.markdown(badges, unsafe_allow_html=True)

    # ── Final decision banner ─────────────────────────────────────────────────
    if final_decision:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        dec_class = {
            "APPROVE":  "decision-approve",
            "REVIEW":   "decision-review",
            "ESCALATE": "decision-escalate",
        }.get(final_decision, "decision-review")
        dec_icon = decision_color(final_decision)
        score    = status_data.get("overall_risk_score", 0)
        band     = status_data.get("risk_band", "")
        total_ms = status_data.get("processing_time_ms") or 0
        st.markdown(
            f'<div class="{dec_class}">'
            f'<h3>{dec_icon} Final Decision: {final_decision}</h3>'
            f'<p><b>Risk Band:</b> {band} &nbsp;|&nbsp; <b>Score:</b> {score}/100 '
            f'&nbsp;|&nbsp; <b>Time:</b> {total_ms:,} ms</p></div>',
            unsafe_allow_html=True,
        )
        if status_data.get("human_review_required") and not status_data.get("human_decision"):
            st.warning("⏳ This case is awaiting analyst review — go to **👤 Human Review Queue**.")
    else:
        if auto_refresh:
            time.sleep(4)
            st.rerun()
