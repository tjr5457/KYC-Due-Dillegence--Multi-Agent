from ..models import KYCState
from ..database import log_audit_event
from ..agents.utils import call_agent_llm
import json

# Hard-escalate regardless of numeric score
_HARD_ESCALATE = {"SANCTIONS_HIT", "DOCUMENT_NOT_AUTHENTIC", "DOCUMENT_INTEGRITY_ISSUE"}

# Force human review queue regardless of numeric score (e.g., for PEP verification)
_FORCE_REVIEW = {"PEP_IDENTIFIED"}


def decision_node(state: KYCState) -> KYCState:
    """Compute final APPROVE / REVIEW / ESCALATE decision with plain-English rationale."""
    print("⚖️   [Decision Node] Computing final decision...")

    score = float(state.get("overall_risk_score") or 0)
    flags = state.get("risk_flags") or []

    hard_escalate_flags = [f for f in flags if f in _HARD_ESCALATE]
    force_review_flags  = [f for f in flags if f in _FORCE_REVIEW]
    low_extraction      = state["confidence_scores"].get("data_extraction", 1.0) < 0.6

    if hard_escalate_flags or low_extraction:
        decision     = "ESCALATE"
        human_review = True
    elif score > 75:
        decision     = "ESCALATE"
        human_review = True
    elif score >= 45 or force_review_flags:
        decision     = "REVIEW"
        human_review = True
    else:
        decision     = "APPROVE"
        human_review = False

    # ── Recommended actions ───────────────────────────────────────────────────
    actions = []
    if "SANCTIONS_HIT" in flags:
        actions.append("Freeze application immediately and notify the compliance team.")
        actions.append("File a Suspicious Activity Report (SAR) per regulatory requirements.")
    if "PEP_IDENTIFIED" in flags:
        actions.append("Apply Enhanced Due Diligence (EDD) procedures.")
        actions.append("Obtain senior management approval before proceeding.")
    if any(f in flags for f in ["DOCUMENT_NOT_AUTHENTIC", "DOCUMENT_INTEGRITY_ISSUE"]):
        actions.append("Request original documents for in-person verification.")
        actions.append("Refer to fraud investigation unit.")
    if "IMPLAUSIBLE_SOURCE_OF_FUNDS" in flags:
        actions.append("Request supporting financial documents (bank statements, ITR).")
    if "HIGH_RISK_INDUSTRY" in flags:
        actions.append("Conduct industry-specific enhanced due diligence.")
    if "NAME_MISMATCH" in flags:
        actions.append("Verify identity documents against government database.")
    if not actions:
        if decision == "APPROVE":
            actions = [
                "Proceed with standard onboarding.",
                "Set periodic review at 12 months.",
            ]
        elif decision == "REVIEW":
            actions = [
                "Assign to KYC analyst for manual review.",
                "Request additional supporting documents.",
            ]

    # ── Plain-English rationale (LLM generated) ───────────────────────────────
    agent_input = {
        "decision": decision,
        "score": score,
        "flags": flags,
        "extraction": state.get("extraction_result", {}),
        "financial": state.get("financial_profile", {})
    }
    schema = '{\n  "human_narrative": "<3-4 sentence plain-English conversational story explaining exactly why this decision/score was given. Example: Customer is 18 years old claiming 50L income from Crypto, which is highly implausible.>"\n}'
    
    print("     [Decision Node] Generating plain-English narrative...")
    narrative_result = call_agent_llm(
        agent_name="DecisionNarrator",
        agent_role="summarizing the final KYC decision and risk factors into a concise, plain-English story for human analysts",
        output_schema=schema,
        agent_input=json.dumps(agent_input),
        max_tokens=300
    )
    
    human_narrative = narrative_result.get("human_narrative", f"Risk score: {score}/100. Decision: {decision}.")

    state["final_decision"]        = decision
    state["human_review_required"] = human_review
    state["decision_rationale"]    = human_narrative
    state["recommended_actions"]   = actions
    state["current_agent"]         = "DecisionNode"

    icons = {"APPROVE": "✅", "REVIEW": "🟡", "ESCALATE": "🔴"}
    print(f"     {icons[decision]}  Decision: {decision} | Human review: {human_review}")

    log_audit_event(state["customer_id"], "DECISION_MADE", {
        "decision":  decision,
        "score":     score,
        "risk_band": state["risk_band"],
        "flags":     flags,
    })
    return state
