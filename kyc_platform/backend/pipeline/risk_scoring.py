from ..models import KYCState
from ..config import SCORE_WEIGHTS, RISK_BAND_THRESHOLDS, FLAG_SCORE_PENALTIES


def compute_risk_score(state: KYCState) -> KYCState:
    """Compute a weighted, fully explainable risk score from all five agents."""
    print("📊  [Risk Engine] Computing explainable risk score...")

    vrf = state.get("verification_result") or {}
    scr = state.get("screening_result")    or {}
    fin = state.get("financial_profile")   or {}
    ext = state.get("extraction_result")   or {}

    # ── Per-component raw scores (0 = safe, 100 = maximum risk) ──────────────
    comp = {
        "id_verification": min(100.0, (
            100.0 * (1.0 - float(vrf.get("cross_field_consistency_score", 0.5)))
            + (30 if vrf.get("id_authentic") is False else 0)
            + (20 if vrf.get("document_integrity") in ["TAMPERED", "SUSPICIOUS"] else 0)
        )),
        "compliance_screening": min(100.0, (
            (50 if scr.get("sanctions_hit") else 0)
            + (25 if scr.get("pep_status")   else 0)
            + (15 if scr.get("adverse_media") else 0)
            + (10 if scr.get("jurisdiction_risk") == "HIGH" else 0)
        )),
        "financial_profiling": float(fin.get("financial_risk_score", 50)),
        "data_extraction":     min(100.0,
            100.0 * (1.0 - float(state["confidence_scores"].get("data_extraction", 0.5)))
        ),
    }

    # ── Weighted base score ───────────────────────────────────────────────────
    base = sum(comp[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)

    # ── Flag penalties (additive on top of base) ──────────────────────────────
    flag_penalty = sum(
        FLAG_SCORE_PENALTIES.get(f.split(":")[0].strip(), 5)
        for f in state["risk_flags"]
    )

    overall = min(100.0, round(base + flag_penalty, 1))

    # ── Risk band ──────────────────────────────────────────────────────────────
    band = "LOW"
    for band_name, (lo, hi) in RISK_BAND_THRESHOLDS.items():
        if lo <= overall < hi:
            band = band_name
            break

    # ── Evidence trail (one entry per agent) ──────────────────────────────────
    evidence = []

    evidence.append({
        "agent":           "IDVerificationAgent",
        "finding": (
            f"Document {'authentic' if vrf.get('id_authentic') else 'NOT authentic'}. "
            f"Face match: {vrf.get('face_match_score', 'N/A')}. "
            f"Integrity: {vrf.get('document_integrity', 'N/A')}."
        ),
        "impact":          "NEGATIVE" if not vrf.get("id_authentic", True) else "POSITIVE",
        "weight":          SCORE_WEIGHTS["id_verification"],
        "component_score": round(comp["id_verification"], 1),
    })

    findings_scr = []
    if scr.get("sanctions_hit"): findings_scr.append("SANCTIONS HIT")
    if scr.get("pep_status"):    findings_scr.append("PEP IDENTIFIED")
    if scr.get("adverse_media"): findings_scr.append("ADVERSE MEDIA")
    evidence.append({
        "agent":           "ComplianceScreeningAgent",
        "finding":         " | ".join(findings_scr) if findings_scr else "No major compliance flags.",
        "impact":          "NEGATIVE" if findings_scr else "POSITIVE",
        "weight":          SCORE_WEIGHTS["compliance_screening"],
        "component_score": round(comp["compliance_screening"], 1),
    })

    evidence.append({
        "agent":           "FinancialProfileAgent",
        "finding": (
            f"Income band: {fin.get('income_band', 'UNKNOWN')}. "
            f"Source of funds: {fin.get('source_of_funds', 'UNKNOWN')} "
            f"({fin.get('source_of_funds_plausibility', 'UNKNOWN')}). "
            f"High-risk industry: {fin.get('high_risk_industry', False)}."
        ),
        "impact":          "NEGATIVE" if fin.get("source_of_funds_plausibility") == "IMPLAUSIBLE" else "NEUTRAL",
        "weight":          SCORE_WEIGHTS["financial_profiling"],
        "component_score": round(comp["financial_profiling"], 1),
    })

    evidence.append({
        "agent":           "DataExtractorAgent",
        "finding": (
            f"Extraction confidence: {ext.get('confidence', 'UNKNOWN')}. "
            f"Missing fields: {ext.get('missing_fields', [])}."
        ),
        "impact":          "NEGATIVE" if ext.get("confidence") == "LOW" else "NEUTRAL",
        "weight":          SCORE_WEIGHTS["data_extraction"],
        "component_score": round(comp["data_extraction"], 1),
    })

    state["overall_risk_score"] = overall
    state["risk_band"]          = band
    state["evidence_trail"]     = evidence

    print(f"     📈  Score: {overall}/100 | Band: {band} | Flags: {len(state['risk_flags'])}")
    return state
