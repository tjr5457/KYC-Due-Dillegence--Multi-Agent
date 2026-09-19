from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Core KYC State (shared across LangGraph nodes) ──────────────────────────

class KYCState(TypedDict):
    # ── Identity ──
    customer_id:     str
    submitted_at:    str
    input_payload:   Dict[str, Any]

    # ── Agent outputs ──
    extraction_result:  Optional[Dict[str, Any]]
    enrichment_result:  Optional[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    screening_result:   Optional[Dict[str, Any]]
    financial_profile:  Optional[Dict[str, Any]]

    # ── Scoring ──
    agent_logs:        List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    risk_flags:        List[str]

    # ── Decision ──
    overall_risk_score:  Optional[float]
    risk_band:           Optional[str]       # LOW | MEDIUM | HIGH | CRITICAL
    final_decision:      Optional[str]       # APPROVE | REVIEW | ESCALATE
    decision_rationale:  Optional[str]
    evidence_trail:      Optional[List[Dict[str, Any]]]
    recommended_actions: Optional[List[str]]
    processing_time_ms:  Optional[int]

    # ── Human oversight ──
    human_review_required: bool
    human_decision:        Optional[str]     # APPROVE_OVERRIDE | REJECT | REQUEST_MORE_INFO | CONFIRM_ESCALATE
    human_notes:           Optional[str]
    human_reviewed_at:     Optional[str]

    # ── Runtime ──
    current_agent: Optional[str]
    error:         Optional[str]
    extraction_attempts: Optional[int]
    refinement_context:  Optional[str]


def create_initial_state(customer_id: str, input_payload: Dict[str, Any]) -> KYCState:
    """Return a fresh KYCState for a new submission."""
    return KYCState(
        customer_id=customer_id,
        submitted_at=datetime.utcnow().isoformat(),
        input_payload=input_payload,
        extraction_result=None,
        enrichment_result=None,
        verification_result=None,
        screening_result=None,
        financial_profile=None,
        agent_logs=[],
        confidence_scores={},
        risk_flags=[],
        overall_risk_score=None,
        risk_band=None,
        final_decision=None,
        decision_rationale=None,
        evidence_trail=None,
        recommended_actions=None,
        processing_time_ms=None,
        human_review_required=False,
        human_decision=None,
        human_notes=None,
        human_reviewed_at=None,
        current_agent=None,
        error=None,
        extraction_attempts=1,
        refinement_context=None,
    )


# ─── FastAPI Pydantic Models ──────────────────────────────────────────────────

class KYCSubmitRequest(BaseModel):
    full_name:       str
    date_of_birth:   str
    nationality:     str
    address:         str
    document_type:   str
    document_number: str
    email:           Optional[str]  = None
    phone:           Optional[str]  = None
    occupation:      Optional[str]  = None
    income_inr:      Optional[float] = None
    source_of_funds: Optional[str]  = None
    customer_id:     Optional[str]  = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "full_name":       "Aditya Raj Verma",
                "date_of_birth":   "1990-06-15",
                "nationality":     "Indian",
                "address":         "15 Linking Road, Mumbai 400054",
                "document_type":   "PAN",
                "document_number": "ABCDE1234F",
                "email":           "aditya@example.com",
                "phone":           "+919876543210",
                "occupation":      "Software Engineer",
                "income_inr":      1500000,
                "source_of_funds": "Salary",
            }
        }
    }


class HumanReviewRequest(BaseModel):
    decision: str   # APPROVE_OVERRIDE | REJECT | REQUEST_MORE_INFO | CONFIRM_ESCALATE
    notes:    str = ""


class KYCStatusResponse(BaseModel):
    customer_id:            str
    status:                 str
    final_decision:         Optional[str]
    overall_risk_score:     Optional[float]
    risk_band:              Optional[str]
    risk_flags:             List[str]
    human_review_required:  bool
    current_agent:          Optional[str]
    processing_time_ms:     Optional[int]
