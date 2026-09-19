import json
import time as _time

from ..models import KYCState
from ..database import log_audit_event
from .utils import call_agent_llm, add_agent_log

SCHEMA = """
{
  "aliases":                      ["<name variant>"],
  "known_addresses":              ["<address>"],
  "business_links":               ["<company or entity>"],
  "social_signals":               "<summary of notable public presence>",
  "entity_type":                  "<INDIVIDUAL | COMPANY | TRUST>",
  "country_risk":                 "<HIGH | MEDIUM | LOW>",
  "jurisdiction":                 "<primary jurisdiction>",
  "data_confidence_score":        <0.0 to 1.0>,
  "ambiguous_identity_risk":      <true | false>,
  "multiple_identity_candidates": <true | false>,
  "enrichment_notes":             "<key findings>",
  "flags":                        ["<FLAG_NAME>"],
  "confidence":                   "<HIGH | MEDIUM | LOW>"
}
"""


def enrichment_agent(state: KYCState) -> KYCState:
    """AGENT 2 — Cross-reference and enrich extracted identity profile."""
    t0 = _time.time()
    state["current_agent"] = "EnrichmentAgent"
    print("[Agent 2/5] EnrichmentAgent starting...")

    combined = {
        "extracted_identity": state["extraction_result"],
        "original_payload":   state["input_payload"],
        "instruction": (
            "Enrich the extracted identity: identify aliases, known address history, "
            "business connections, and assess country-level risk from the nationality. "
            "Flag ambiguous identity situations or multiple candidate risk."
        ),
    }

    result = call_agent_llm(
        agent_name="EnrichmentAgent",
        agent_role=(
            "cross-referencing and enriching extracted identity data with external signals, "
            "detecting aliases, address history, business links, and country risk."
        ),
        output_schema=SCHEMA,
        agent_input=json.dumps(combined, indent=2),
        max_tokens=700,
    )

    duration_ms = int((_time.time() - t0) * 1000)
    state["enrichment_result"] = result
    state["confidence_scores"]["enrichment"] = float(
        result.get("data_confidence_score", 0.5))

    if result.get("ambiguous_identity_risk"):
        state["risk_flags"].append("AMBIGUOUS_IDENTITY")
    if result.get("country_risk") == "HIGH":
        state["risk_flags"].append("HIGH_RISK_JURISDICTION")
    for flag in result.get("flags", []):
        if flag not in state["risk_flags"]:
            state["risk_flags"].append(flag)

    state = add_agent_log(state, "EnrichmentAgent", result, duration_ms)
    log_audit_event(state["customer_id"], "AGENT_COMPLETED",
                    {"agent": "EnrichmentAgent", "duration_ms": duration_ms,
                     "country_risk": result.get("country_risk")})

    print(
        f"     Done in {duration_ms} ms | Country Risk: {result.get('country_risk', '?')}")
    return state
