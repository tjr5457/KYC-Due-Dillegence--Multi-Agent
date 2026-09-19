from frontend.utils import api_post, page_header
import streamlit as st
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


# Form options
DOC_TYPES   = ["PAN", "AADHAAR", "PASSPORT", "DRIVING_LICENSE"]
FUND_SOURCES = ["Salary", "Business", "Investments", "Inheritance", "Crypto", "Other"]


def _step_progress(current: int):
    """Render a 4-step progress indicator."""
    steps = ["Details", "Document", "Selfie", "Submit"]
    items = []
    for i, label in enumerate(steps, 1):
        if i < current:
            cls = "done"
            circle = "✓"
        elif i == current:
            cls = "active"
            circle = str(i)
        else:
            cls = ""
            circle = str(i)
        items.append(
            f'<div class="step-item {cls}">'
            f'  <div class="step-circle">{circle}</div>'
            f'  <div class="step-label">{label}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div class="step-progress">{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def render():
    page_header(
        title="Customer Onboarding",
        subtitle="Submit a new customer for end-to-end KYC due diligence",
        icon="🧾",
    )

    # Multi-step flow: 1) Details, 2) Document upload, 3) Photo upload, 4) Review & Submit
    step = st.session_state.get("onboarding_step", 1)
    if step <= 4:
        _step_progress(step)

    # ── Step 1: Customer Details ──────────────────────────────────────────────
    if step == 1:
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:1rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.08em;margin:1rem 0 0.75rem;">Step 1 — Customer Details</h3>',
            unsafe_allow_html=True,
        )

        with st.form("kyc_details", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                full_name     = st.text_input("Full Legal Name *", placeholder="e.g. John Doe")
                date_of_birth = st.text_input("Date of Birth * (YYYY-MM-DD)", placeholder="e.g. 1985-10-25")
                nationality   = st.text_input("Nationality *", placeholder="e.g. Indian")
                email         = st.text_input("Email", placeholder="john.doe@example.com")
                phone         = st.text_input("Phone", placeholder="+91 98765 43210")
            with c2:
                document_type   = st.selectbox("Document Type *", DOC_TYPES)
                document_number = st.text_input("Document Number *", placeholder="e.g. ABCDE1234F")
                occupation      = st.text_input("Occupation", placeholder="e.g. Software Engineer")
                income_inr_str  = st.text_input("Annual Income", value="", placeholder="e.g. 1500000")
                source_of_funds = st.selectbox("Source of Funds", FUND_SOURCES)

            address = st.text_area("Address *", height=68, placeholder="Enter full residential address...")

            st.markdown("<br>", unsafe_allow_html=True)
            
            _, col_submit = st.columns([4, 1])
            with col_submit:
                submitted = st.form_submit_button("Next →", use_container_width=True)
            if submitted:
                try:
                    income_inr = float(income_inr_str.replace(",", "")) if income_inr_str else 0.0
                except ValueError:
                    income_inr = -1.0

                if not full_name or not date_of_birth or not nationality or not address or not document_number:
                    st.error("Please fill in all required (*) fields before continuing.")
                elif income_inr < 0:
                    st.error("Please enter a valid positive number for Annual Income.")
                else:
                    st.session_state["kyc_payload"] = {
                        "full_name":       full_name,
                        "date_of_birth":   date_of_birth,
                        "nationality":     nationality,
                        "address":         address,
                        "document_type":   document_type,
                        "document_number": document_number,
                        "email":           email or None,
                        "phone":           phone or None,
                        "occupation":      occupation or None,
                        "income_inr":      income_inr if income_inr > 0 else None,
                        "source_of_funds": source_of_funds,
                        "customer_id":     None,
                    }
                    st.session_state["onboarding_step"] = 2
                    st.rerun()

    # ── Step 2: Document Upload ───────────────────────────────────────────────
    elif step == 2:
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:1rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.08em;margin:1rem 0 0.75rem;">Step 2 — Document Upload</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#64748b;margin-bottom:1rem;">Upload the customer\'s identity document (PDF or image).</p>',
            unsafe_allow_html=True,
        )
        uploaded_doc = st.file_uploader(
            "Upload identity document",
            type=["pdf", "png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        col_back, _, col_next = st.columns([1, 3, 1])
        with col_back:
            if st.button("← Back", use_container_width=True):
                st.session_state["onboarding_step"] = 1
                st.rerun()
        with col_next:
            if st.button("Next →", use_container_width=True):
                if not uploaded_doc:
                    st.error("Please upload a document before continuing.")
                else:
                    st.session_state["uploaded_document"] = uploaded_doc.getvalue()
                    st.session_state["onboarding_step"] = 3
                    st.rerun()

    # ── Step 3: Selfie Upload ─────────────────────────────────────────────────
    elif step == 3:
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:1rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.08em;margin:1rem 0 0.75rem;">Step 3 — Photo / Selfie Upload</h3>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#64748b;margin-bottom:1rem;">Upload a selfie photo of the customer for verification.</p>',
            unsafe_allow_html=True,
        )
        uploaded_photo = st.file_uploader(
            "Upload selfie",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=False,
        )
        col_back, _, col_next = st.columns([1, 3, 1])
        with col_back:
            if st.button("← Back", use_container_width=True):
                st.session_state["onboarding_step"] = 2
                st.rerun()
        with col_next:
            if st.button("Next →", use_container_width=True):
                if not uploaded_photo:
                    st.error("Please upload a selfie before continuing.")
                else:
                    st.session_state["uploaded_photo"] = uploaded_photo.getvalue()
                    st.session_state["onboarding_step"] = 4
                    st.rerun()

    # ── Step 4: Review & Submit ─────────────────────────────────────────────
    elif step == 4:
        st.markdown(
            '<h3 style="color:#94a3b8;font-size:1rem;font-weight:600;text-transform:uppercase;'
            'letter-spacing:0.08em;margin:1rem 0 0.75rem;">Step 4 — Review & Submit</h3>',
            unsafe_allow_html=True,
        )
        payload = st.session_state.get("kyc_payload", {})

        # Display a clean review table
        st.markdown(
            '<p style="color:#64748b;margin-bottom:0.75rem;">Review customer details before submitting to the KYC pipeline.</p>',
            unsafe_allow_html=True,
        )

        if payload:
            col_a, col_b = st.columns(2)
            fields_left  = list(payload.items())[:6]
            fields_right = list(payload.items())[6:]
            with col_a:
                for k, v in fields_left:
                    st.markdown(
                        f'<div style="margin-bottom:0.5rem;">'
                        f'<span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#475569;">{k.replace("_"," ").title()}</span><br>'
                        f'<span style="color:#f1f5f9;font-weight:500;">{v or "—"}</span></div>',
                        unsafe_allow_html=True,
                    )
            with col_b:
                for k, v in fields_right:
                    st.markdown(
                        f'<div style="margin-bottom:0.5rem;">'
                        f'<span style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.08em;color:#475569;">{k.replace("_"," ").title()}</span><br>'
                        f'<span style="color:#f1f5f9;font-weight:500;">{v or "—"}</span></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown("<br>", unsafe_allow_html=True)
        col_back, _, col_submit = st.columns([1, 2, 1])
        with col_back:
            if st.button("← Back", use_container_width=True):
                st.session_state["onboarding_step"] = 3
                st.rerun()
        with col_submit:
            if st.button("🚀 Submit for KYC", use_container_width=True, type="primary"):
                if not payload:
                    st.error("No customer details found — restart the onboarding flow.")
                else:
                    with st.spinner("Submitting to KYC intelligence pipeline…"):
                        result = api_post("/kyc/submit", payload)
                    if result:
                        cid    = result.get("customer_id", "")
                        status = result.get("status", "processing")

                        st.session_state["active_customer_id"] = cid
                        st.session_state["submitted_cid"]       = cid
                        st.session_state["submitted_status"]    = status
                        st.session_state["onboarding_step"]     = 5  # go to success screen
                        st.session_state.pop("kyc_payload", None)
                        st.session_state.pop("uploaded_document", None)
                        st.session_state.pop("uploaded_photo", None)
                        st.rerun()

    # ── Step 5: Success Screen ──────────────────────────────────────────────
    elif step == 5:
        cid    = st.session_state.get("submitted_cid", "")
        status = st.session_state.get("submitted_status", "processing")

        # ── Centered success card using native Streamlit columns ──────
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_card, _ = st.columns([1, 2, 1])
        with col_card:
            st.markdown(
                f"""
                <div style="
                    text-align: center;
                    padding: 2.5rem 2rem;
                    background: rgba(16,185,129,0.07);
                    border: 1px solid rgba(16,185,129,0.3);
                    border-radius: 20px;
                    box-shadow: 0 0 40px rgba(16,185,129,0.08);
                ">
                    <div style="font-size:3.5rem;margin-bottom:1rem;">✅</div>
                    <div style="font-size:1.5rem;font-weight:800;color:#a7f3d0;
                        letter-spacing:0.01em;margin-bottom:0.4rem;">
                        KYC Submitted Successfully!
                    </div>
                    <div style="font-size:0.9rem;color:#6ee7b7;margin-bottom:2rem;">
                        Your case is now in the AI pipeline
                    </div>
                    <div style="display:flex;justify-content:center;gap:1rem;
                        flex-wrap:wrap;margin-bottom:2rem;">
                        <div style="background:rgba(0,0,0,0.25);border-radius:12px;
                            padding:0.8rem 1.5rem;min-width:130px;">
                            <div style="font-size:0.6rem;text-transform:uppercase;
                                letter-spacing:0.1em;color:#6ee7b7;font-weight:600;
                                margin-bottom:0.3rem;">Customer ID</div>
                            <div style="font-size:1rem;font-weight:700;color:#f1f5f9;
                                font-family:'JetBrains Mono',monospace;">{cid}</div>
                        </div>
                        <div style="background:rgba(0,0,0,0.25);border-radius:12px;
                            padding:0.8rem 1.5rem;min-width:130px;">
                            <div style="font-size:0.6rem;text-transform:uppercase;
                                letter-spacing:0.1em;color:#6ee7b7;font-weight:600;
                                margin-bottom:0.3rem;">Pipeline Status</div>
                            <div style="font-size:1rem;font-weight:700;color:#fde68a;
                                text-transform:uppercase;">
                                ● {status}
                            </div>
                        </div>
                    </div>
                    <div style="background:rgba(0,212,255,0.06);
                        border:1px solid rgba(0,212,255,0.15);
                        border-radius:10px;padding:0.9rem 1.2rem;
                        font-size:0.85rem;color:#94a3b8;line-height:1.6;">
                        ⚡ Your case is now running through the <b style='color:#00d4ff;'>AI agent pipeline</b>.<br>
                        Navigate to <b style='color:#00d4ff;'>⚡ Live Pipeline</b> in the sidebar
                        to watch each agent process the case in real time.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_l, btn_r = st.columns(2)
        with btn_l:
            if st.button("➕ Submit Another Customer", use_container_width=True):
                st.session_state["onboarding_step"] = 1
                st.session_state.pop("submitted_cid", None)
                st.session_state.pop("submitted_status", None)
                st.rerun()
        with btn_r:
            if st.button("⚡ Go to Live Pipeline →", use_container_width=True, type="primary"):
                # Navigate via the sidebar radio — key is the widget label ("nav")
                st.session_state["nav"] = "⚡ Live Pipeline"
                st.rerun()

