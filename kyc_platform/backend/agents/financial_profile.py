import json
import time as _time

from ..models import KYCState
from ..database import log_audit_event
from ..config import HIGH_RISK_INDUSTRIES
from .utils import call_agent_llm, add_agent_log

SCHEMA = """
{
  "income_band":                  "<LOW(<3L) | LOWER_MIDDLE(3-7L) | MIDDLE(7-15L) | UPPER_MIDDLE(15-30L) | HIGH(>30L)>",
  "income_declared_inr":          <number or null>,
  "source_of_funds":              "<Salary | Business | Investments | Inheritance | Crypto | Unknown>",
  "source_of_funds_plausibility": "<PLAUSIBLE | QUESTIONABLE | IMPLAUSIBLE>",
  "source_of_funds_notes":        "<explanation>",
  "transaction_patterns":         "<expected transaction behaviour based on profile>",
  "high_risk_industry":           <true | false>,
  "industry_risk_notes":          "<e.g. 'Cryptocurrency — high risk'>",
  "pep_financial_exposure":       <true | false>,
  "unusual_wealth_indicators":    ["<indicator>"],
  "financial_risk_score":         <0 to 100>,
  "risk_factors":                 ["<factor>"],
  "flags":                        ["<FLAG_NAME>"],
  "confidence":                   "<HIGH | MEDIUM | LOW>"
}
"""


def financial_profile_agent(state: KYCState) -> KYCState:
    """AGENT 5 — Assess financial risk profile of the customer."""
    t0 = _time.time()
    state["current_agent"] = "FinancialProfileAgent"
    print("[Agent 5/5] FinancialProfileAgent starting...")

    ext = state["extraction_result"] or {}
    enr = state["enrichment_result"] or {}
    scr = state["screening_result"] or {}

    occupation = (ext.get("occupation") or "").lower()
    industry_risk = any(ind in occupation for ind in HIGH_RISK_INDUSTRIES)

    combined = {
        "financial_data": {
            "income_declared": ext.get("income_declared"),
            "source_of_funds": ext.get("source_of_funds"),
            "occupation":      ext.get("occupation"),
            "nationality":     ext.get("nationality"),
        },
        "enrichment_signals": {
            "business_links": enr.get("business_links", []),
            "country_risk":   enr.get("country_risk"),
        },
        "compliance_signals": {
            "pep_status":        scr.get("pep_status"),
            "jurisdiction_risk": scr.get("jurisdiction_risk"),
        },
        "rule_based_checks": {
            "occupation_in_high_risk_industry": industry_risk,
        },
        "instruction": (
            "Assess this customer's financial risk profile. "
            "Evaluate plausibility of declared income vs occupation. "
            "Score financial risk 0 (no risk) to 100 (extreme risk). "
            "Flag implausible income, missing financial data, or high-risk industry exposure."
        ),
    }

    result = call_agent_llm(
        agent_name="FinancialProfileAgent",
        agent_role=(
            "assessing customer financial risk based on declared income, "
            "source of funds, occupation, and financial behaviour patterns."
        ),
        output_schema=SCHEMA,
        agent_input=json.dumps(combined, indent=2),
        max_tokens=700,
    )

    duration_ms = int((_time.time() - t0) * 1000)
    state["financial_profile"] = result
    state["confidence_scores"]["financial_profiling"] = max(
        0.0, 1.0 - (float(result.get("financial_risk_score", 50)) / 100)
    )

    if result.get("source_of_funds_plausibility") == "IMPLAUSIBLE":
        state["risk_flags"].append("IMPLAUSIBLE_SOURCE_OF_FUNDS")
    if result.get("high_risk_industry"):
        state["risk_flags"].append("HIGH_RISK_INDUSTRY")
    for flag in result.get("flags", []):
        if flag not in state["risk_flags"]:
            state["risk_flags"].append(flag)

    state = add_agent_log(state, "FinancialProfileAgent", result, duration_ms)
    log_audit_event(state["customer_id"], "AGENT_COMPLETED",
                    {"agent": "FinancialProfileAgent", "duration_ms": duration_ms,
                     "financial_risk_score": result.get("financial_risk_score"),
                     "income_band":          result.get("income_band")})

    print(f"     Done in {duration_ms} ms | Financial Risk: {result.get('financial_risk_score')} "
          f"| Income Band: {result.get('income_band')}")
    return state
