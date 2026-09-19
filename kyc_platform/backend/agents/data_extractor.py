import json
import time as _time

from ..models import KYCState
from ..database import log_audit_event
from .utils import call_agent_llm, add_agent_log

SCHEMA = """
{
  "name":                    "<full legal name>",
  "dob":                     "<YYYY-MM-DD or null>",
  "address":                 "<full address or null>",
  "id_number":               "<document ID number>",
  "document_type":           "<PAN | AADHAAR | PASSPORT | DRIVING_LICENSE>",
  "nationality":             "<country name>",
  "submitted_docs":          ["<doc type>"],
  "email":                   "<email or null>",
  "phone":                   "<phone or null>",
  "occupation":              "<occupation or null>",
  "income_declared":         "<numeric amount in INR or null>",
  "source_of_funds":         "<Salary | Business | Investments | Inheritance | Crypto | Unknown>",
  "missing_fields":          ["<field name>"],
  "low_confidence_fields":   ["<field name>"],
  "extraction_notes":        "<anomalies or issues noticed>",
  "confidence":              "<HIGH | MEDIUM | LOW>",
  "confidence_score":        <0.0 to 1.0>
}
"""


def data_extractor_agent(state: KYCState) -> KYCState:
    """AGENT 1 — Parse raw onboarding payload into structured identity fields."""
    t0 = _time.time()
    state["current_agent"] = "DataExtractorAgent"
    print("[Agent 1/5] DataExtractorAgent starting...")

    role = (
        "parsing and extracting structured identity data from raw customer onboarding input. "
        "Identify all identity fields, flag missing data, and self-assess extraction confidence."
    )
    
    inp_payload = dict(state["input_payload"])
    if state.get("refinement_context"):
        role += (
            " NOTE: A name mismatch was detected in a prior verification run. Re-examine the raw "
            f"onboarding input carefully to extract the name, using this context: {state['refinement_context']}. "
            "Resolve any differences in nicknames, initials, middle names, or titles to match the ID document name."
        )
        inp_payload["refinement_feedback"] = state["refinement_context"]
        print(f"     [Refinement Attempt] Appending feedback: {state['refinement_context']}")

    result = call_agent_llm(
        agent_name="DataExtractorAgent",
        agent_role=role,
        output_schema=SCHEMA,
        agent_input=json.dumps(inp_payload, indent=2),
        max_tokens=700,
    )

    duration_ms = int((_time.time() - t0) * 1000)
    state["extraction_result"] = result
    state["confidence_scores"]["data_extraction"] = float(
        result.get("confidence_score", 0.5))

    if result.get("confidence_score", 1.0) < 0.6:
        state["risk_flags"].append("LOW_EXTRACTION_CONFIDENCE")

    state = add_agent_log(state, "DataExtractorAgent", result, duration_ms)
    log_audit_event(state["customer_id"], "AGENT_COMPLETED",
                    {"agent": "DataExtractorAgent", "duration_ms": duration_ms,
                     "confidence": result.get("confidence")})

    print(
        f"     Done in {duration_ms} ms | Confidence: {result.get('confidence', '?')}")
    if result.get("missing_fields"):
        print(f"     Missing: {result['missing_fields']}")

    return state
