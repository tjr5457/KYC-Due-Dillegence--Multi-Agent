import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from ..models import KYCSubmitRequest, HumanReviewRequest, create_initial_state
from ..database import init_db, save_state, load_state, list_cases, log_audit_event, get_audit_log, clear_audit_log
from ..pipeline.runner import run_kyc_pipeline, submit_human_review
from ..config import MODEL_NAME, VLLM_HOST
from ..agents.utils import call_agent_llm

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DN Agentic KYC Intelligence Platform",
    description=(
        "Multi-agent KYC due diligence powered by AMD ROCm / vLLM / LangGraph. "
        "Performs data extraction, enrichment, ID verification, compliance screening, "
        "and financial profiling — then emits an explainable APPROVE / REVIEW / ESCALATE decision."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ─── Background runner ────────────────────────────────────────────────────────

def _run_bg(payload: dict, customer_id: str):
    try:
        run_kyc_pipeline(payload, customer_id)
    except Exception as exc:
        state = load_state(customer_id)
        if state:
            state["error"] = str(exc)
            state["final_decision"] = "ESCALATE"
            state["human_review_required"] = True
            state["current_agent"] = "ERROR"
            save_state(state)
        log_audit_event(customer_id, "PIPELINE_ERROR", {"error": str(exc)})
        print(f"❌  Pipeline error for {customer_id}: {exc}")


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.post("/kyc/submit", tags=["KYC"], summary="Submit a new KYC case")
async def submit_kyc(request: KYCSubmitRequest, background_tasks: BackgroundTasks):
    """
    Submit a customer for end-to-end KYC due diligence.
    The pipeline runs asynchronously — poll `/kyc/status/{customer_id}` for results.
    """
    if request.customer_id:
        customer_id = request.customer_id
    else:
        # Generate sequential ID (e.g. KYC_001)
        cases = list_cases()
        next_num = len(cases) + 1
        customer_id = f"KYC_{next_num:03d}"

    payload = {
        "full_name":       request.full_name,
        "date_of_birth":   request.date_of_birth,
        "nationality":     request.nationality,
        "address":         request.address,
        "document_type":   request.document_type,
        "document_number": request.document_number,
        "email":           request.email,
        "phone":           request.phone,
        "occupation":      request.occupation,
        "income_inr":      request.income_inr,
        "source_of_funds": request.source_of_funds,
    }

    # Persist immediately so /status works right away
    initial = create_initial_state(customer_id, payload)
    save_state(initial)

    background_tasks.add_task(_run_bg, payload, customer_id)

    return {
        "message":     "KYC submission accepted. Pipeline running in background.",
        "customer_id": customer_id,
        "status":      "processing",
        "poll_url":    f"/kyc/status/{customer_id}",
    }


@app.get("/kyc/status/{customer_id}", tags=["KYC"], summary="Poll pipeline status")
async def get_status(customer_id: str):
    """Lightweight status endpoint — safe to poll every few seconds."""
    state = load_state(customer_id)
    if not state:
        raise HTTPException(
            status_code=404, detail=f"No case found: {customer_id}")

    pending_review = (
        state.get("human_review_required")
        and not state.get("human_decision")
    )
    status = "awaiting_review" if pending_review else (
        state.get("final_decision") or "processing")

    return {
        "customer_id":           customer_id,
        "status":                status,
        "final_decision":        state.get("final_decision"),
        "overall_risk_score":    state.get("overall_risk_score"),
        "risk_band":             state.get("risk_band"),
        "risk_flags":            state.get("risk_flags", []),
        "human_review_required": state.get("human_review_required"),
        "human_decision":        state.get("human_decision"),
        "current_agent":         state.get("current_agent"),
        "processing_time_ms":    state.get("processing_time_ms"),
        "agent_count":           len(state.get("agent_logs", [])),
        "error":                 state.get("error"),
    }


@app.get("/kyc/report/{customer_id}", tags=["KYC"], summary="Full explainable report")
async def get_report(customer_id: str):
    """Return the full KYC report including evidence trail, agent outputs, and confidence scores."""
    state = load_state(customer_id)
    if not state:
        raise HTTPException(
            status_code=404, detail=f"No case found: {customer_id}")

    return {
        "customer_id":           customer_id,
        "submitted_at":          state.get("submitted_at"),
        "decision":              state.get("final_decision"),
        "overall_risk_score":    state.get("overall_risk_score"),
        "risk_band":             state.get("risk_band"),
        "decision_rationale":    state.get("decision_rationale"),
        "evidence_trail":        state.get("evidence_trail"),
        "flags":                 state.get("risk_flags", []),
        "recommended_actions":   state.get("recommended_actions", []),
        "human_review_required": state.get("human_review_required"),
        "human_decision":        state.get("human_decision"),
        "human_notes":           state.get("human_notes"),
        "human_reviewed_at":     state.get("human_reviewed_at"),
        "agent_logs":            state.get("agent_logs", []),
        "confidence_scores":     state.get("confidence_scores", {}),
        "processing_time_ms":    state.get("processing_time_ms"),
        "extraction_result":     state.get("extraction_result"),
        "enrichment_result":     state.get("enrichment_result"),
        "verification_result":   state.get("verification_result"),
        "screening_result":      state.get("screening_result"),
        "financial_profile":     state.get("financial_profile"),
        "error":                 state.get("error"),
    }


@app.post("/kyc/human-review/{customer_id}", tags=["Human Review"],
          summary="Submit analyst review decision")
async def human_review(customer_id: str, request: HumanReviewRequest):
    """
    Record an analyst's decision for a REVIEW or ESCALATE case.
    decision: APPROVE_OVERRIDE | REJECT | REQUEST_MORE_INFO | CONFIRM_ESCALATE
    """
    try:
        submit_human_review(customer_id, request.decision, request.notes)
        return {
            "message":        "Human review recorded successfully.",
            "customer_id":    customer_id,
            "human_decision": request.decision,
            "notes":          request.notes,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/kyc/cases", tags=["KYC"], summary="List all KYC cases")
async def list_kyc_cases(status: Optional[str] = None):
    """List all cases. Optionally filter by status (e.g. APPROVE, REVIEW, ESCALATE, processing)."""
    cases = list_cases(status)
    return {
        "total": len(cases),
        "cases": [
            {
                "customer_id":           c.get("customer_id"),
                "final_decision":        c.get("final_decision"),
                "overall_risk_score":    c.get("overall_risk_score"),
                "risk_band":             c.get("risk_band"),
                "human_review_required": c.get("human_review_required"),
                "human_decision":        c.get("human_decision"),
                "submitted_at":          c.get("submitted_at"),
                "flags_count":           len(c.get("risk_flags", [])),
            }
            for c in cases
        ],
    }


@app.get("/kyc/audit-log", tags=["Audit"], summary="Get audit log")
async def get_audit(customer_id: Optional[str] = None):
    """Return the immutable audit log. Optionally filter by customer_id."""
    return get_audit_log(customer_id)


@app.delete("/kyc/audit-log", tags=["Audit"], summary="Clear audit log")
async def clear_audit():
    """Clear all audit log entries."""
    clear_audit_log()
    return {"message": "Audit log cleared successfully"}


@app.get("/llm_health", tags=["LLM"], summary="Check LLM connectivity and basic response")
async def llm_health():
    """Perform a minimal LLM call to verify connectivity and model responsiveness."""
    try:
        result = call_agent_llm(
            agent_name="health-check",
            agent_role="respond with a single JSON field status",
            output_schema='{"status":"string"}',
            agent_input='Please return {"status":"ok"} if reachable',
            max_tokens=32,
        )
        ok = "error" not in result
        return {
            "ok": ok,
            "model": MODEL_NAME,
            "host": VLLM_HOST,
            "result": result,
        }
    except Exception as exc:
        return {"ok": False, "model": MODEL_NAME, "host": VLLM_HOST, "error": str(exc)}


@app.get("/health", tags=["System"], summary="Health check")
async def health():
    return {"status": "healthy", "service": "DN KYC Intelligence Platform v1.0"}
