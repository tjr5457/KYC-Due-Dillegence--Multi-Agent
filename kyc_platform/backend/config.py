import os
# Load .env at import time so config values are available in any process
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ─── AMD ROCm / vLLM inference ─────────────────────────────────────────────
# Keep the inference path ROCm/vLLM-first for the notebook migration and hackathon demo.
MODEL_NAME = os.getenv(
    "KYC_MODEL_NAME",
    os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.2"),
)

# vLLM OpenAI-compatible endpoint (AMD ROCm server)
VLLM_HOST = os.getenv("VLLM_HOST", "http://localhost:8000")

# API key optional for protected or proxied vLLM endpoints.
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "token-amd-kyc")

# ─── Database ─────────────────────────────────────────────────────────────────
DB_PATH = os.getenv("KYC_DB_PATH", "kyc_platform.db")

# ─── Ports ────────────────────────────────────────────────────────────────────
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT",   "8001"))
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8502"))

# ─── Risk Scoring Weights (must sum to 1.0) ───────────────────────────────────
SCORE_WEIGHTS = {
    "id_verification":      0.25,   # 25 %
    "compliance_screening": 0.35,   # 35 %
    "financial_profiling":  0.25,   # 25 %
    "data_extraction":      0.15,   # 15 %
}

# ─── Risk Band Thresholds (score range → band label) ─────────────────────────
RISK_BAND_THRESHOLDS = {
    "LOW":      (0,   45),
    "MEDIUM":   (45,  75),
    "HIGH":     (75,  90),
    "CRITICAL": (90, 101),
}

# ─── Flag → extra score penalty ───────────────────────────────────────────────
FLAG_SCORE_PENALTIES = {
    "SANCTIONS_HIT":               40,
    "DOCUMENT_NOT_AUTHENTIC":      35,
    "DOCUMENT_INTEGRITY_ISSUE":    30,
    "PEP_IDENTIFIED":              20,
    "NAME_MISMATCH":               20,
    "IMPLAUSIBLE_SOURCE_OF_FUNDS": 20,
    "AMBIGUOUS_IDENTITY":          15,
    "HIGH_RISK_JURISDICTION":      15,
    "LOW_EXTRACTION_CONFIDENCE":   15,
    "ADVERSE_MEDIA":               15,
    "HIGH_RISK_INDUSTRY":          10,
    "DOCUMENT_EXPIRED":            10,
}

# ─── High-risk industries ─────────────────────────────────────────────────────
HIGH_RISK_INDUSTRIES = [
    "cryptocurrency", "crypto", "gambling", "casino", "arms", "weapons",
    "real estate", "forex", "money transfer", "hawala", "shell company",
    "mining", "oil", "offshore",
]

# ─── Mock sanctions / PEP lists (stand-in for real-world databases) ───────────
MOCK_SANCTIONS_LIST = [
    "Viktor Petrov",
    "Ahmad Al-Rashid",
    "Carlos Mendez Fuentes",
    "Liu Wei Hong",
    "Dmitri Volkov",
    "Kevin Ross",
]

MOCK_PEP_LIST = [
    "Rajendra Kumar Singh",
    "Rahul Mehta",
]
