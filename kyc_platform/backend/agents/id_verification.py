import re
import json
import time as _time

from ..models import KYCState
from ..database import log_audit_event
from .utils import call_agent_llm, add_agent_log

SCHEMA = """
{
  "id_authentic":                   <true | false>,
  "face_match_score":               <0.0 to 1.0>,
  "document_integrity":             "<INTACT | TAMPERED | SUSPICIOUS | UNVERIFIABLE>",
  "expiry_valid":                   <true | false | null>,
  "expiry_date":                    "<YYYY-MM-DD or null>",
  "cross_field_consistency_score":  <0.0 to 1.0>,
  "name_match":                     <true | false>,
  "dob_match":                      <true | false>,
  "id_number_valid_format":         <true | false>,
  "document_type_verified":         "<PAN | AADHAAR | PASSPORT | DRIVING_LICENSE>",
  "anomalies_detected":             ["<anomaly description>"],
  "verification_notes":             "<key findings>",
  "flags":                          ["<FLAG_NAME>"],
  "confidence":                     "<HIGH | MEDIUM | LOW>"
}
"""


def _valid_pan(pan: str) -> bool:
    """PAN: 5 letters + 4 digits + 1 letter  e.g. ABCDE1234F"""
    return bool(re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan.upper())) if pan else False


def _valid_aadhaar(uid: str) -> bool:
    """Aadhaar: 12 digits, first not 0 or 1"""
    clean = re.sub(r"[\s\-]", "", str(uid))
    return bool(re.match(r"^[2-9][0-9]{11}$", clean)) if uid else False


def id_verification_agent(state: KYCState) -> KYCState:
    """AGENT 3 — Verify document authenticity and cross-field consistency."""
    t0 = _time.time()
    state["current_agent"] = "IDVerificationAgent"
    print("[Agent 3/5] IDVerificationAgent starting...")

    ext = state["extraction_result"] or {}
    enr = state["enrichment_result"] or {}

    id_num = ext.get("id_number", "")
    doc_type = ext.get("document_type", "")

    if doc_type == "PAN":
        fmt_ok = _valid_pan(id_num)
    elif doc_type == "AADHAAR":
        fmt_ok = _valid_aadhaar(id_num)
    else:
        fmt_ok = len(str(id_num)) >= 6

    combined = {
        "extracted_identity": ext,
        "enrichment_profile": enr,
        "rule_based_checks":  {
            "id_format_valid":  fmt_ok,
            "document_type":    doc_type,
            "id_number":        id_num,
            "submitted_name":   state["input_payload"].get("name") or state["input_payload"].get("full_name") or "",
        },
        "instruction": (
            f"Verify the submitted {doc_type} document. Check cross-field consistency "
            "(name, DOB, address matches between extraction and enrichment). "
            f"Note: rule-based format check = {fmt_ok}. "
            "Simulate face-match score (0.85+ = good). "
            "Flag tampering, expiry issues, or name mismatches."
        ),
    }

    result = call_agent_llm(
        agent_name="IDVerificationAgent",
        agent_role=(
            "verifying document authenticity, cross-field consistency, "
            "detecting tampering, and assessing face-match likelihood."
        ),
        output_schema=SCHEMA,
        agent_input=json.dumps(combined, indent=2),
        max_tokens=700,
    )

    duration_ms = int((_time.time() - t0) * 1000)
    state["verification_result"] = result
    state["confidence_scores"]["id_verification"] = float(
        result.get("cross_field_consistency_score", 0.5)
    )

    if result.get("id_authentic") is False:
        state["risk_flags"].append("DOCUMENT_NOT_AUTHENTIC")
    if result.get("document_integrity") in ["TAMPERED", "SUSPICIOUS"]:
        state["risk_flags"].append("DOCUMENT_INTEGRITY_ISSUE")
    if result.get("expiry_valid") is False:
        state["risk_flags"].append("DOCUMENT_EXPIRED")
    if result.get("name_match") is False:
        state["risk_flags"].append("NAME_MISMATCH")
    for a in result.get("anomalies_detected", []):
        flag = f"ANOMALY:{a[:40].upper().replace(' ', '_')}"
        if flag not in state["risk_flags"]:
            state["risk_flags"].append(flag)

    state = add_agent_log(state, "IDVerificationAgent", result, duration_ms)
    log_audit_event(state["customer_id"], "AGENT_COMPLETED",
                    {"agent": "IDVerificationAgent", "duration_ms": duration_ms,
                     "authentic": result.get("id_authentic"),
                     "face_match": result.get("face_match_score")})

    print(f"     Done in {duration_ms} ms | Authentic: {result.get('id_authentic')} "
          f"| Face match: {result.get('face_match_score')}")
    return state
