import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
import pandas as pd

from frontend.utils import api_get, api_post, decision_color, page_header
from frontend.pdf_generator import generate_kyc_pdf_report

ANALYST_DECISIONS = [
    "APPROVE_OVERRIDE",
    "REJECT",
    "REQUEST_MORE_INFO",
    "CONFIRM_ESCALATE",
]

DECISION_LABELS = {
    "APPROVE_OVERRIDE":  "✅ Approve Override — manually clear the case",
    "REJECT":            "❌ Reject — deny customer onboarding",
    "REQUEST_MORE_INFO": "📋 Request More Info — ask customer for docs",
    "CONFIRM_ESCALATE":  "🔴 Confirm Escalate — forward to compliance team",
}

DECISION_COLORS = {
    "APPROVE_OVERRIDE":  "#10b981",
    "REJECT":            "#ef4444",
    "REQUEST_MORE_INFO": "#3b82f6",
    "CONFIRM_ESCALATE":  "#f59e0b",
}


def render_case_details(selected_cid, case, show_form=True):
    ai_dec    = case.get("final_decision", "REVIEW")
    dec_icon  = decision_color(ai_dec)
    score     = case.get("overall_risk_score", "N/A")
    band      = case.get("risk_band", "—")
    flags_cnt = case.get("flags_count", 0)

    st.markdown(f"### {dec_icon} Case Details: **{selected_cid}**")
    st.markdown(f"<p style='color:#94a3b8; font-size:0.9rem;'>AI Decision: <b>{ai_dec}</b> | Score: <b>{score}</b> | Band: <b>{band}</b> | Flags: <b>{flags_cnt}</b></p>", unsafe_allow_html=True)
    
    report = api_get(f"/kyc/report/{selected_cid}")
    if report:
        col1, col2 = st.columns([10, 1])
        with col2:
            pdf_bytes = generate_kyc_pdf_report(selected_cid, report)
            st.markdown("""
                <style>
                div[data-testid="stDownloadButton"] button {
                    background-color: #3b82f6 !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 6px !important;
                    padding: 8px 16px !important;
                    float: right !important;
                }
                div[data-testid="stDownloadButton"] button:hover {
                    background-color: #2563eb !important;
                    color: white !important;
                }
                </style>
            """, unsafe_allow_html=True)
            st.download_button(
                label="📥", 
                data=pdf_bytes, 
                file_name=f"{selected_cid}_Report.pdf", 
                mime="application/pdf", 
                use_container_width=False,
                key=f"dl_{selected_cid}_{'form' if show_form else 'exp'}"
            )
            
        # Rationale
        st.markdown(
            f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;'
            f'padding:0.75rem 1rem;margin-bottom:0.75rem;">'
            f'<span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#475569;">AI Rationale</span><br>'
            f'<span style="color:#cbd5e1;">{report.get("decision_rationale", "—")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Flags
        if report.get("flags"):
            badges = " ".join(
                f'<span class="flag-badge">{f}</span>' for f in report["flags"]
            )
            st.markdown(badges, unsafe_allow_html=True)
            st.markdown("")

        # Agent evidence summary
        evidence = report.get("evidence_trail") or []
        if evidence:
            html = '<div style="margin-top:1rem;font-size:0.75rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">🔍 Evidence Summary</div>'
            html += '<div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;border:1px solid rgba(255,255,255,0.05);">'
            for ev in evidence:
                impact_icon = {"NEGATIVE": "🔴", "POSITIVE": "🟢", "NEUTRAL": "⚪"}.get(
                    ev.get("impact"), "⚪"
                )
                agent_name = ev.get("agent", "Unknown")
                finding = ev.get("finding", "—")
                html += f'<div style="margin-bottom:0.4rem;font-size:0.85rem;">{impact_icon} <b>{agent_name}</b> &mdash; <span style="color:#94a3b8;">{finding}</span></div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        # Recommended actions
        if report.get("recommended_actions"):
            html = '<div style="margin-top:0.5rem;font-size:0.75rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">📋 Recommended Actions</div>'
            html += '<div style="background:rgba(0,0,0,0.2);border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;border:1px solid rgba(255,255,255,0.05);">'
            for a in report["recommended_actions"]:
                html += f'<div style="margin-bottom:0.3rem;font-size:0.85rem;"><span style="color:#38bdf8;font-weight:700;">&bull;</span> <span style="color:#cbd5e1;">{a}</span></div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

    if show_form:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<p style="font-size:0.8rem;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Analyst Decision</p>',
            unsafe_allow_html=True,
        )

        with st.form(key=f"form_{selected_cid}"):
            decision_key = st.selectbox(
                "Select action",
                ANALYST_DECISIONS,
                format_func=lambda x: DECISION_LABELS[x]
            )
            notes = st.text_area(
                "Analyst Notes / Justification",
                placeholder="Document your review rationale here…",
                height=80,
            )

            submitted = st.form_submit_button(f"✅ Submit Decision for {selected_cid}", type="primary", use_container_width=True)
            if submitted:
                result = api_post(
                    f"/kyc/human-review/{selected_cid}",
                    {"decision": decision_key, "notes": notes},
                )
                if result:
                    st.success(f"Decision **{decision_key}** recorded for {selected_cid}.")
                    st.rerun()


def render():
    page_header(
        title="Human Review Queue",
        subtitle="Cases flagged for analyst decision (REVIEW / ESCALATE outcomes)",
        icon="👤",
    )

    all_cases_data = api_get("/kyc/cases") or {"cases": []}
    all_cases      = all_cases_data.get("cases", [])

    pending  = [c for c in all_cases if c.get("human_review_required") and not c.get("human_decision")]
    reviewed = [c for c in all_cases if c.get("human_decision")]
    approved = [c for c in all_cases if c.get("final_decision") == "APPROVE"]

    # ── KPI Row ───────────────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#f59e0b;">'
            f'<div class="kpi-icon">⏳</div>'
            f'<div class="kpi-value">{len(pending)}</div>'
            f'<div class="kpi-label">Pending Review</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#10b981;">'
            f'<div class="kpi-icon">✅</div>'
            f'<div class="kpi-value">{len(reviewed)}</div>'
            f'<div class="kpi-label">Reviewed</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#00d4ff;">'
            f'<div class="kpi-icon">🟢</div>'
            f'<div class="kpi-value">{len(approved)}</div>'
            f'<div class="kpi-label">Auto-Approved</div></div>',
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#7c3aed;">'
            f'<div class="kpi-icon">📦</div>'
            f'<div class="kpi-value">{len(all_cases)}</div>'
            f'<div class="kpi-label">Total Cases</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["⏳ Pending Queue", "📂 Case Explorer & PDF Export"])

    with tab1:
        if not pending:
            st.markdown(
                '<div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.2);'
                'border-radius:12px;padding:1.5rem;text-align:center;">'
                '<div style="font-size:2rem;margin-bottom:0.5rem;">✅</div>'
                '<p style="color:#10b981;font-weight:600;margin:0;">No cases pending human review</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            case_options = {
                c["customer_id"]: f"{c['customer_id']} — {c.get('final_decision', 'REVIEW')} (Score: {c.get('overall_risk_score', 'N/A')})"
                for c in pending
            }
            selected_cid = st.selectbox(
                "Select a case to review:",
                options=list(case_options.keys()),
                format_func=lambda x: case_options[x],
                key="pending_select_box"
            )
            if selected_cid:
                case = next((c for c in pending if c["customer_id"] == selected_cid), None)
                if case:
                    render_case_details(selected_cid, case, show_form=True)

    with tab2:
        if not all_cases:
            st.markdown(
                '<div style="background:rgba(255,255,255,0.03);border-radius:12px;padding:1.5rem;text-align:center;">'
                '<p style="color:#64748b;margin:0;">No cases available in the system yet.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            all_case_options = {
                c["customer_id"]: f"{c['customer_id']} — {c.get('final_decision', 'UNKNOWN')} (Score: {c.get('overall_risk_score', 'N/A')}) ({c.get('human_decision') or 'No Analyst Decision'})"
                for c in all_cases
            }
            explorer_cid = st.selectbox(
                "Select any case in the system to inspect or export PDF report:",
                options=list(all_case_options.keys()),
                format_func=lambda x: all_case_options[x],
                key="explorer_select_box"
            )
            if explorer_cid:
                case = next((c for c in all_cases if c["customer_id"] == explorer_cid), None)
                if case:
                    render_case_details(explorer_cid, case, show_form=False)

    # ── Reviewed cases table ──────────────────────────────────────────────────
    if reviewed:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.1em;margin:0 0 0.75rem;">✅ Reviewed Cases</h3>',
            unsafe_allow_html=True,
        )
        df = pd.DataFrame([
            {
                "Customer ID":      c["customer_id"],
                "AI Decision":      c.get("final_decision"),
                "Risk Score":       c.get("overall_risk_score"),
                "Risk Band":        c.get("risk_band"),
                "Analyst Decision": c.get("human_decision"),
            }
            for c in reviewed
        ])
        st.dataframe(df, use_container_width=True)
