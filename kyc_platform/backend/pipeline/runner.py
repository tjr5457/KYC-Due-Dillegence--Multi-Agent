import uuid
import time as _time
from datetime import datetime
from typing import Optional, Dict, Any

from ..models import KYCState, create_initial_state
from ..database import save_state, load_state, log_audit_event
from .graph import kyc_graph


def run_kyc_pipeline(
    input_payload: Dict[str, Any],
    customer_id:   Optional[str] = None,
) -> KYCState:
    """
    Execute the full 5-agent KYC pipeline for a customer submission.
    Returns the final KYCState with decision, score, and evidence trail.
    """
    if not customer_id:
        customer_id = f"KYC-{uuid.uuid4().hex[:8].upper()}"

    divider = "=" * 62
    print(f"\n{divider}")
    print(f"  KYC PIPELINE STARTED  |  Customer: {customer_id}")
    print(divider)

    t_total = _time.time()

    # Normalize input payload keys to match the extractor schema
    normalized_payload = {}
    mapping = {
        "full_name": "name",
        "date_of_birth": "dob",
        "document_number": "id_number",
        "income_inr": "income_declared"
    }
    for k, v in input_payload.items():
        new_key = mapping.get(k, k)
        normalized_payload[new_key] = v

    initial = create_initial_state(customer_id, normalized_payload)
    save_state(initial)
    log_audit_event(customer_id, "PIPELINE_STARTED", {
        "payload_keys": list(normalized_payload.keys()),
    })

    final: KYCState = kyc_graph.invoke(initial)

    total_ms = int((_time.time() - t_total) * 1000)
    final["processing_time_ms"] = total_ms
    save_state(final)

    log_audit_event(customer_id, "PIPELINE_COMPLETED", {
        "decision":  final.get("final_decision"),
        "score":     final.get("overall_risk_score"),
        "band":      final.get("risk_band"),
        "total_ms":  total_ms,
    })

    print(divider)
    dec = final.get("final_decision", "?")
    print(f"  Decision: {dec} | Score: {final.get('overall_risk_score')} "
          f"| Band: {final.get('risk_band')} | {total_ms:,} ms")
    print(divider + "\n")

    return final


def submit_human_review(customer_id: str, decision: str, notes: str = "") -> KYCState:
    """
    Record an analyst's review decision for a REVIEW / ESCALATE case.
    decision must be one of: APPROVE_OVERRIDE | REJECT | REQUEST_MORE_INFO | CONFIRM_ESCALATE
    """
    state = load_state(customer_id)
    if not state:
        raise ValueError(f"No case found for customer_id: {customer_id}")

    valid = {"APPROVE_OVERRIDE", "REJECT",
             "REQUEST_MORE_INFO", "CONFIRM_ESCALATE"}
    if decision not in valid:
        raise ValueError(
            f"Invalid decision '{decision}'. Must be one of: {valid}")

    state["human_decision"] = decision
    state["human_notes"] = notes
    state["human_reviewed_at"] = datetime.utcnow().isoformat()
    save_state(state)

    log_audit_event(customer_id, "HUMAN_REVIEW_SUBMITTED", {
        "decision": decision,
        "notes":    notes,
    })
    print(f"✅  Human review recorded | {customer_id}: {decision}")
    return state
