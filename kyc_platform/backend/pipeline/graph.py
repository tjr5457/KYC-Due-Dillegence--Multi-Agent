import time as _time
import copy
from concurrent.futures import ThreadPoolExecutor

from langgraph.graph import StateGraph, END

from ..models import KYCState
from ..database import save_state, log_audit_event
from ..agents.data_extractor import data_extractor_agent
from ..agents.enrichment import enrichment_agent
from ..agents.id_verification import id_verification_agent
from ..agents.compliance_screening import compliance_screening_agent
from ..agents.financial_profile import financial_profile_agent
from .risk_scoring import compute_risk_score
from .decision import decision_node


# ─── Conditional edges ────────────────────────────────────────────────────────

def _route_after_extraction(state: KYCState) -> str:
    """Short-circuit to risk scoring if extraction confidence is critically low."""
    if state["confidence_scores"].get("data_extraction", 1.0) < 0.4:
        print("     ⚡  Short-circuit: extraction confidence critically low → skip to risk scoring")
        return "risk_scoring"
    return "parallel_agents"


def _route_after_parallel(state: KYCState) -> str:
    """Check if name mismatch occurred and route back to extraction if allowed, otherwise proceed."""
    ver_res = state.get("verification_result") or {}
    name_ok = ver_res.get("name_match", True)
    attempts = state.get("extraction_attempts", 1) or 1
    
    if name_ok is False and attempts < 2:
        extracted_name = (state.get("extraction_result") or {}).get("name", "Unknown")
        submitted_name = state["input_payload"].get("name") or state["input_payload"].get("full_name") or "Unknown"
        state["refinement_context"] = (
            f"Name mismatch detected. The document extractor extracted the name '{extracted_name}', "
            f"but the submitted legal name is '{submitted_name}'. Please re-examine the document payload "
            "and extract the correct legal name matching the submitted details."
        )
        state["extraction_attempts"] = attempts + 1
        print(f"     ⚡  Self-Correction Loop: Name mismatch detected ('{extracted_name}' vs '{submitted_name}'). "
              f"Routing back to 'extraction' for refinement (Attempt {attempts + 1})...")
        
        # Clear previous result payloads to run them fresh
        state["extraction_result"] = None
        state["enrichment_result"] = None
        state["verification_result"] = None
        state["screening_result"] = None
        return "extraction"
        
    if (state.get("screening_result") or {}).get("sanctions_hit"):
        print("     ⚡  Short-circuit: SANCTIONS_HIT → skip financial profiling")
        return "risk_scoring"
    return "financial_profile_step"


def _route_after_decision(state: KYCState) -> str:
    return "human_oversight" if state.get("human_review_required") else END


# ─── Human oversight node (non-blocking pause) ───────────────────────────────

def _human_oversight(state: KYCState) -> KYCState:
    state["current_agent"] = "HumanOversightNode"
    save_state(state)
    log_audit_event(state["customer_id"], "AWAITING_HUMAN_REVIEW", {
        "ai_decision": state.get("final_decision"),
        "score":       state.get("overall_risk_score"),
        "flags":       state.get("risk_flags"),
    })
    print(
        f"⏸️   [Human Oversight] Case {state['customer_id']} queued for analyst review")
    return state


# ─── Parallel Execution wrapper node ─────────────────────────────────────────

def parallel_agents_node(state: KYCState) -> KYCState:
    print("[Parallel Step] Executing Enrichment, ID Verification, and Compliance Screening in parallel...")
    t0 = _time.time()
    
    # Run tasks concurrently in separate threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_enr = executor.submit(enrichment_agent, copy.deepcopy(state))
        future_ver = executor.submit(id_verification_agent, copy.deepcopy(state))
        future_scr = executor.submit(compliance_screening_agent, copy.deepcopy(state))
        
        state_enr = future_enr.result()
        state_ver = future_ver.result()
        state_scr = future_scr.result()
        
    # Merge payload dictionaries back to the main state
    state["enrichment_result"] = state_enr.get("enrichment_result")
    state["verification_result"] = state_ver.get("verification_result")
    state["screening_result"] = state_scr.get("screening_result")
    
    # Merge unique risk flags
    state["risk_flags"] = list(set(
        state.get("risk_flags", []) +
        state_enr.get("risk_flags", []) +
        state_ver.get("risk_flags", []) +
        state_scr.get("risk_flags", [])
    ))
    
    # Merge agent logs
    state["agent_logs"] = (
        state.get("agent_logs", []) +
        state_enr.get("agent_logs", []) +
        state_ver.get("agent_logs", []) +
        state_scr.get("agent_logs", [])
    )
    
    # Merge confidence scores
    state["confidence_scores"].update(state_enr.get("confidence_scores", {}))
    state["confidence_scores"].update(state_ver.get("confidence_scores", {}))
    state["confidence_scores"].update(state_scr.get("confidence_scores", {}))
    
    duration_ms = int((_time.time() - t0) * 1000)
    print(f"[Parallel Step] All 3 agents completed in {duration_ms} ms")
    return state


# ─── Risk + decision combined wrapper ────────────────────────────────────────

def _risk_and_decide(state: KYCState) -> KYCState:
    t0 = _time.time()
    state = compute_risk_score(state)
    state = decision_node(state)
    state["processing_time_ms"] = int((_time.time() - t0) * 1000)
    save_state(state)
    return state


# ─── Build & compile the LangGraph ───────────────────────────────────────────

def _build() -> StateGraph:
    g = StateGraph(KYCState)

    g.add_node("extraction",              data_extractor_agent)
    g.add_node("parallel_agents",         parallel_agents_node)
    g.add_node("financial_profile_step",  financial_profile_agent)
    g.add_node("risk_scoring",            _risk_and_decide)
    g.add_node("human_oversight",         _human_oversight)

    g.set_entry_point("extraction")

    g.add_conditional_edges(
        "extraction",
        _route_after_extraction,
        {"parallel_agents": "parallel_agents", "risk_scoring": "risk_scoring"},
    )
    g.add_conditional_edges(
        "parallel_agents",
        _route_after_parallel,
        {
            "extraction": "extraction",
            "financial_profile_step": "financial_profile_step",
            "risk_scoring": "risk_scoring"
        }
    )
    g.add_edge("financial_profile_step", "risk_scoring")
    g.add_conditional_edges(
        "risk_scoring",
        _route_after_decision,
        {"human_oversight": "human_oversight", END: END},
    )
    g.add_edge("human_oversight", END)

    return g.compile()


# Compiled singleton — imported by runner.py
kyc_graph = _build()
print("KYC LangGraph compiled")
print("    Flow: extraction -> [enrichment || id_verification || screening] -> financial_profile -> risk_scoring -> [human_oversight] -> END")
