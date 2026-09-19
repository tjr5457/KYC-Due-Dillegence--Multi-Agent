import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
import plotly.express as px
import pandas as pd

from frontend.utils import api_get, api_delete, page_header

EVENT_COLORS = {
    "PIPELINE_STARTED":       "#00d4ff",
    "AGENT_COMPLETED":        "#10b981",
    "DECISION_MADE":          "#7c3aed",
    "AWAITING_HUMAN_REVIEW":  "#f59e0b",
    "HUMAN_REVIEW_SUBMITTED": "#f97316",
    "PIPELINE_COMPLETED":     "#3b82f6",
}

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "Inter", "color": "#94a3b8"},
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)"),
)


def render():
    page_header(
        title="Audit Log",
        subtitle="Immutable record of all KYC events, agent completions, and decisions",
        icon="📋",
    )

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])
    with col1:
        customer_filter = st.text_input(
            "Filter by Customer ID (leave blank for all)",
            placeholder="e.g. KYC-GREEN-001",
        )
    with col2:
        event_filter = st.selectbox(
            "Filter by Event Type",
            ["ALL", "PIPELINE_STARTED", "AGENT_COMPLETED", "DECISION_MADE",
             "AWAITING_HUMAN_REVIEW", "HUMAN_REVIEW_SUBMITTED", "PIPELINE_COMPLETED"],
        )
        
    c1, c2 = st.columns([8, 2])
    with c2:
        if st.button("🗑️ Reset Logs", use_container_width=True):
            res = api_delete("/kyc/audit-log")
            if res:
                st.success("Audit log reset successfully!")
                st.rerun()

    path = "/kyc/audit-log"
    if customer_filter.strip():
        path += f"?customer_id={customer_filter.strip()}"

    logs = api_get(path) or []

    if event_filter != "ALL":
        logs = [l for l in logs if l["event_type"] == event_filter]

    if not logs:
        st.markdown(
            '<div style="text-align:center;padding:3rem;color:#334155;">'
            '<div style="font-size:3rem;margin-bottom:1rem;">📋</div>'
            '<p style="font-size:1rem;color:#475569;">No audit events found. Submit a KYC case to generate audit entries.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    # ── KPI Row ───────────────────────────────────────────────────────────────
    decisions    = [l for l in logs if l["event_type"] == "DECISION_MADE"]
    unique_cases = len({l["customer_id"] for l in logs})

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#00d4ff;">'
            f'<div class="kpi-icon">📊</div>'
            f'<div class="kpi-value">{len(logs)}</div>'
            f'<div class="kpi-label">Total Events</div></div>',
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#7c3aed;">'
            f'<div class="kpi-icon">🆔</div>'
            f'<div class="kpi-value">{unique_cases}</div>'
            f'<div class="kpi-label">Unique Cases</div></div>',
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f'<div class="kpi-card" style="--kpi-color:#10b981;">'
            f'<div class="kpi-icon">⚖️</div>'
            f'<div class="kpi-value">{len(decisions)}</div>'
            f'<div class="kpi-label">Decisions Made</div></div>',
            unsafe_allow_html=True,
        )

    # ── Main log table ────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    table_html = '''<div style="max-height:400px;overflow-y:auto;border:1px solid rgba(255,255,255,0.1);border-radius:8px;background:rgba(0,0,0,0.2);">
<table style="width:100%;border-collapse:collapse;text-align:left;font-size:0.8rem;color:#e2e8f0;">
<thead style="position:sticky;top:0;background:#0f172a;z-index:1;border-bottom:1px solid rgba(255,255,255,0.1);">
<tr>
<th style="padding:0.75rem 1rem;color:#94a3b8;font-weight:600;">ID</th>
<th style="padding:0.75rem 1rem;color:#94a3b8;font-weight:600;">Timestamp</th>
<th style="padding:0.75rem 1rem;color:#94a3b8;font-weight:600;">Customer ID</th>
<th style="padding:0.75rem 1rem;color:#94a3b8;font-weight:600;">Event</th>
<th style="padding:0.75rem 1rem;color:#94a3b8;font-weight:600;">Details</th>
</tr>
</thead>
<tbody>'''
    
    for l in logs:
        details_str = json.dumps(l["event_data"])[:150]
        table_html += f'''<tr style="border-bottom:1px solid rgba(255,255,255,0.05); transition: background 0.2s;">
<td style="padding:0.6rem 1rem;">{l["id"]}</td>
<td style="padding:0.6rem 1rem;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#94a3b8;">{l["timestamp"]}</td>
<td style="padding:0.6rem 1rem;font-weight:600;color:#38bdf8;">{l["customer_id"]}</td>
<td style="padding:0.6rem 1rem;"><span style="background:rgba(255,255,255,0.05);padding:0.2rem 0.5rem;border-radius:4px;font-size:0.7rem;">{l["event_type"]}</span></td>
<td style="padding:0.6rem 1rem;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#cbd5e1;word-break:break-all;">{details_str}</td>
</tr>'''
        
    table_html += '''</tbody>
</table>
</div>'''
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown(
        f'<p style="font-size:0.7rem;color:#475569;text-align:right;margin-top:0.25rem;">Showing {len(logs)} events</p>',
        unsafe_allow_html=True,
    )

    # ── Charts ────────────────────────────────────────────────────────────────
    if decisions and not customer_filter:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        ch1, ch2 = st.columns(2)

        # Decision distribution pie
        d_counts: dict = {}
        for d in decisions:
            dec = d["event_data"].get("decision", "UNKNOWN")
            d_counts[dec] = d_counts.get(dec, 0) + 1

        with ch1:
            st.markdown(
                '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
                'letter-spacing:0.1em;margin:0 0 0.75rem;">Decision Outcomes</h3>',
                unsafe_allow_html=True,
            )
            fig_pie = px.pie(
                values=list(d_counts.values()),
                names=list(d_counts.keys()),
                color=list(d_counts.keys()),
                color_discrete_map={
                    "APPROVE":  "#10b981",
                    "REVIEW":   "#f59e0b",
                    "ESCALATE": "#ef4444",
                    "UNKNOWN":  "#475569",
                },
                hole=0.45,
            )
            fig_pie.update_traces(
                textfont_color="#f1f5f9",
                marker_line_color="rgba(0,0,0,0.3)",
                marker_line_width=2,
            )
            fig_pie.update_layout(
                height=300,
                showlegend=True,
                legend=dict(font=dict(color="#94a3b8")),
                **_DARK_LAYOUT,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Risk score histogram
        scores = [
            float(d["event_data"].get("score", 0))
            for d in decisions
            if d["event_data"].get("score") is not None
        ]
        with ch2:
            st.markdown(
                '<h3 style="color:#94a3b8;font-size:0.8rem;font-weight:600;text-transform:uppercase;'
                'letter-spacing:0.1em;margin:0 0 0.75rem;">Risk Score Distribution</h3>',
                unsafe_allow_html=True,
            )
            if scores:
                fig_hist = px.histogram(
                    x=scores,
                    nbins=10,
                    labels={"x": "Risk Score"},
                    color_discrete_sequence=["#7c3aed"],
                )
                fig_hist.add_vline(x=45, line_dash="dash", line_color="#10b981",
                                   annotation_text="Approve", annotation_font_color="#10b981")
                fig_hist.add_vline(x=75, line_dash="dash", line_color="#ef4444",
                                   annotation_text="Escalate", annotation_font_color="#ef4444")
                fig_hist.update_traces(marker_line_width=0, opacity=0.85)
                fig_hist.update_layout(height=300, **_DARK_LAYOUT)
                st.plotly_chart(fig_hist, use_container_width=True)

    # Event timeline removed as requested
