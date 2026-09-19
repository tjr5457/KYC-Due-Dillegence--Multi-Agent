import json
import time as _time
from typing import Optional, List

from ..models import KYCState
from ..database import log_audit_event
from ..config import MOCK_SANCTIONS_LIST, MOCK_PEP_LIST
from .utils import call_agent_llm, add_agent_log

SCHEMA = """
{
  "sanctions_hit":          <true | false>,
  "sanctions_details":      "<matched list entry if any, else null>",
  "pep_status":             <true | false>,
  "pep_details":            "<PEP category e.g. senior_official, family_member — or null>",
  "adverse_media":          <true | false>,
  "adverse_media_summary":  "<brief summary if found, else null>",
  "watchlist_matches":      ["<list_name: match detail>"],
  "risk_flags":             ["<FLAG_NAME>"],
  "jurisdiction_risk":      "<HIGH | MEDIUM | LOW>",
  "screening_confidence":   <0.0 to 1.0>,
  "partial_match_details":  "<fuzzy / partial match details if any>",
  "screening_notes":        "<overall findings>",
  "confidence":             "<HIGH | MEDIUM | LOW>"
}
"""


def _fuzzy_match(name: str, name_list: List[str], threshold: float = 0.75) -> Optional[str]:
    """Token-overlap fuzzy name matching (no external dependency)."""
    if not name:
        return None
    tokens = set(name.lower().split())
    for candidate in name_list:
        cand_tokens = set(candidate.lower().split())
        if not cand_tokens:
            continue
        overlap = len(tokens & cand_tokens) / len(cand_tokens)
        if overlap >= threshold:
            return candidate
    return None


def compliance_screening_agent(state: KYCState) -> KYCState:
    """AGENT 4 — Screen against sanctions lists, PEP databases, watchlists."""
    t0 = _time.time()
    state["current_agent"] = "ComplianceScreeningAgent"
    print("[Agent 4/5] ComplianceScreeningAgent starting...")

    ext = state["extraction_result"] or {}
    enr = state["enrichment_result"] or {}

    name = ext.get("name", "")
    aliases = enr.get("aliases", [])
    all_names = [name] + aliases

    sanctions_match: Optional[str] = None
    pep_match:       Optional[str] = None
    for n in all_names:
        if not sanctions_match:
            sanctions_match = _fuzzy_match(n, MOCK_SANCTIONS_LIST)
        if not pep_match:
            pep_match = _fuzzy_match(n, MOCK_PEP_LIST)

    combined = {
        "identity_profile": {
            "name":           name,
            "aliases":        aliases,
            "nationality":    ext.get("nationality"),
            "dob":            ext.get("dob"),
            "occupation":     ext.get("occupation"),
            "business_links": enr.get("business_links", []),
            "country_risk":   enr.get("country_risk"),
            "jurisdiction":   enr.get("jurisdiction"),
        },
        "rule_based_pre_checks": {
            "sanctions_list_match": sanctions_match,
            "pep_list_match":       pep_match,
        },
        "instruction": (
            "Screen this individual against global sanctions, PEP databases, and adverse media. "
            "Incorporate findings from rule_based_pre_checks: if sanctions_list_match is not null, sanctions_hit MUST be true. "
            "If pep_list_match is not null, pep_status MUST be true. "
            "If a pre-check match is null, do NOT flag it. "
            "Assess jurisdiction risk from nationality and flag partial matches too."
        ),
    }

    result = call_agent_llm(
        agent_name="ComplianceScreeningAgent",
        agent_role=(
            "screening individuals against sanctions lists, PEP databases, "
            "adverse media, and watchlists to identify compliance risks."
        ),
        output_schema=SCHEMA,
        agent_input=json.dumps(combined, indent=2),
        max_tokens=700,
    )

    duration_ms = int((_time.time() - t0) * 1000)

    # Deterministic pre-check override (guard against LLM failures)
    if sanctions_match:
        result["sanctions_hit"] = True
        result["sanctions_details"] = result.get("sanctions_details") or f"Matched: {sanctions_match}"
    if pep_match:
        result["pep_status"] = True
        result["pep_details"] = result.get("pep_details") or f"Matched: {pep_match}"

    state["screening_result"] = result
    state["confidence_scores"]["compliance_screening"] = float(
        result.get("screening_confidence", 0.5)
    )

    if result.get("sanctions_hit"):
        state["risk_flags"].append("SANCTIONS_HIT")
    if result.get("pep_status"):
        state["risk_flags"].append("PEP_IDENTIFIED")
    if result.get("adverse_media"):
        state["risk_flags"].append("ADVERSE_MEDIA")
    for flag in result.get("risk_flags", []):
        if flag not in state["risk_flags"]:
            state["risk_flags"].append(flag)

    state = add_agent_log(
        state, "ComplianceScreeningAgent", result, duration_ms)
    log_audit_event(state["customer_id"], "AGENT_COMPLETED",
                    {"agent": "ComplianceScreeningAgent", "duration_ms": duration_ms,
                     "sanctions_hit": result.get("sanctions_hit"),
                     "pep_status":    result.get("pep_status")})

    print(f"     Done in {duration_ms} ms | Sanctions: {result.get('sanctions_hit')} "
          f"| PEP: {result.get('pep_status')}")
    return state
