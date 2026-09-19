# 🏦 DN KYC Platform

**AMD ROCm · vLLM · LangGraph · FastAPI**

---

## Navigation

- Customer Onboarding
- Live Pipeline
- Risk Dashboard
- Human Review Queue
- Audit Log

---

**Decision thresholds**

- 🟢 Score < 45 → APPROVE
- 🟡 Score 45–75 → REVIEW
- 🔴 Score > 75 → ESCALATE

**TCS AMD Hackathon 2025**

> DN agentic KYC intelligence will be center of the page

---

## Quick Start — 3 Terminal Windows

### 1 · Install Python dependencies

```bash
pip install -r kyc_platform/requirements.txt
```

### 2 · Start vLLM inference server (Terminal 1) — requires AMD GPU

```bash
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --host  0.0.0.0 \
  --port  8000 \
  --dtype float16 \
  --max-model-len 4096 \
  --gpu-memory-utilization 0.85 \
  --api-key token-amd-kyc
```

> **AMD ROCm wheel:** `pip install vllm --extra-index-url https://download.pytorch.org/whl/rocm6.0`

### 3 · Start FastAPI backend (Terminal 2)

```bash
cd kyc_platform
python run_backend.py
# → http://localhost:8001
# → http://localhost:8001/docs   (Swagger UI)
```

### 4 · Start Streamlit frontend (Terminal 3)

```bash
cd kyc_platform
python run_frontend.py
# → http://localhost:8502
```

---

## Project Structure

```
kyc_platform/
│
├── backend/                         ← FastAPI + LangGraph (no UI code here)
│   ├── config.py                    ← Model name, ports, risk weights, penalties
│   ├── models.py                    ← KYCState TypedDict + Pydantic API models
│   ├── database.py                  ← SQLite: init, save/load state, audit log
│   ├── main.py                      ← app export for uvicorn
│   │
│   ├── agents/                      ← One file per LLM agent
│   │   ├── utils.py                 ← call_agent_llm(), add_agent_log()
│   │   ├── data_extractor.py        ← Agent 1: parse identity fields
│   │   ├── enrichment.py            ← Agent 2: enrich & cross-reference
│   │   ├── id_verification.py       ← Agent 3: verify document authenticity
│   │   ├── compliance_screening.py  ← Agent 4: sanctions / PEP / watchlist
│   │   └── financial_profile.py     ← Agent 5: financial risk profiling
│   │
│   ├── pipeline/
│   │   ├── risk_scoring.py          ← Weighted scoring + evidence trail
│   │   ├── decision.py              ← APPROVE / REVIEW / ESCALATE logic
│   │   ├── graph.py                 ← LangGraph DAG (build + compile)
│   │   └── runner.py                ← run_kyc_pipeline(), submit_human_review()
│   │
│   └── api/
│       └── routes.py                ← All 7 FastAPI endpoints
│
├── frontend/                        ← Streamlit UI (no business logic here)
│   ├── config.py                    ← API_BASE URL
│   ├── utils.py                     ← api_get/post, risk_gauge chart, CSS
│   ├── app.py                       ← Entry point — page config + sidebar nav
│   └── pages/
│       ├── onboarding.py            ← Page 1: submission form + demo presets
│       ├── live_pipeline.py         ← Page 2: real-time agent pipeline monitor
│       ├── risk_dashboard.py        ← Page 3: score gauge + evidence trail
│       ├── human_review.py          ← Page 4: analyst review queue
│       └── audit_log.py             ← Page 5: audit log + decision charts
│
├── run_backend.py                   ← Start uvicorn on port 8001
├── run_frontend.py                  ← Start Streamlit on port 8502
└── requirements.txt
```

---

## API Reference

| Method | Endpoint                          | Description                                      |
| ------ | --------------------------------- | ------------------------------------------------ |
| `POST` | `/kyc/submit`                     | Submit new customer for KYC                      |
| `GET`  | `/kyc/status/{customer_id}`       | Poll pipeline status                             |
| `GET`  | `/kyc/report/{customer_id}`       | Full explainable report                          |
| `POST` | `/kyc/human-review/{customer_id}` | Analyst submits decision                         |
| `GET`  | `/kyc/cases`                      | List all cases (optional `?status=` filter)      |
| `GET`  | `/kyc/audit-log`                  | Full audit log (optional `?customer_id=` filter) |
| `GET`  | `/health`                         | Health check                                     |

---

## Decision Logic

| Condition                        | Decision                                   |
| -------------------------------- | ------------------------------------------ |
| Score < 45 AND no critical flags | ✅ **APPROVE** (automatic)                 |
| Score 45–75                      | 🟡 **REVIEW** (human-in-the-loop)          |
| Score > 75                       | 🔴 **ESCALATE** (automatic)                |
| `SANCTIONS_HIT`                  | 🔴 **ESCALATE** (immediate, ignores score) |
| `DOCUMENT_NOT_AUTHENTIC`         | 🔴 **ESCALATE** (immediate, ignores score) |
| `DOCUMENT_INTEGRITY_ISSUE`       | 🔴 **ESCALATE** (immediate, ignores score) |
| Extraction confidence < 60%      | 🔴 **ESCALATE** (automatic)                |

## Risk Score Composition

| Agent                | Weight  | What it measures                    |
| -------------------- | ------- | ----------------------------------- |
| Compliance Screening | **35%** | Sanctions / PEP / adverse media     |
| ID Verification      | **25%** | Document authenticity + consistency |
| Financial Profiling  | **25%** | Income plausibility + industry risk |
| Data Extraction      | **15%** | Extraction confidence completeness  |

Score is then adjusted upward by flag penalties (e.g. +40 for SANCTIONS_HIT, +35 for DOCUMENT_NOT_AUTHENTIC).

---

## Demo Scenarios (pre-filled in the Onboarding page)

| Button        | Customer                                                     | Expected Outcome |
| ------------- | ------------------------------------------------------------ | ---------------- |
| 🟢 Green Case | Aditya Raj Verma — Indian software engineer, PAN card        | **APPROVE**      |
| 🟡 Amber Case | Rajendra Kumar Singh — Government official (PEP list match)  | **REVIEW**       |
| 🔴 Red Case   | Viktor Petrov — Crypto trader, Russian, sanctions list match | **ESCALATE**     |

---

## Environment Variables

| Variable         | Default                              | Description                 |
| ---------------- | ------------------------------------ | --------------------------- |
| `KYC_MODEL_NAME` | `mistralai/Mistral-7B-Instruct-v0.2` | vLLM model to use           |
| `VLLM_HOST`      | `http://localhost:8000`              | vLLM server URL             |
| `VLLM_API_KEY`   | `token-amd-kyc`                      | vLLM API key (local only)   |
| `KYC_DB_PATH`    | `kyc_platform.db`                    | SQLite database path        |
| `FASTAPI_PORT`   | `8001`                               | Backend port                |
| `STREAMLIT_PORT` | `8502`                               | Frontend port               |
| `KYC_API_BASE`   | `http://localhost:8001`              | Frontend → Backend base URL |

---

## Human Review Decisions

An analyst reviewing a flagged case can submit one of four decisions:

| Decision            | Meaning                                     |
| ------------------- | ------------------------------------------- |
| `APPROVE_OVERRIDE`  | Manually clear — override AI recommendation |
| `REJECT`            | Deny customer onboarding entirely           |
| `REQUEST_MORE_INFO` | Ask customer to submit additional documents |
| `CONFIRM_ESCALATE`  | Confirm escalation to compliance team       |
