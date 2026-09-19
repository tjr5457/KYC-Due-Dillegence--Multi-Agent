"""
DN Agentic KYC Intelligence Platform — Backend entry point.

Run from the kyc_platform/ directory:
    cd kyc_platform
    python run_backend.py
"""

from backend.config import FASTAPI_PORT
import uvicorn
import sys
import os

# Ensure kyc_platform/ is on the path so 'backend' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Load .env file if present so env vars can be provided via a file (no PowerShell needed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; if not installed users can still set real env vars
    pass

# Import config after loading .env so env values are respected at import time


if __name__ == "__main__":
    print("=" * 60)
    print("DN Agentic KYC Intelligence Platform — Backend")
    print(f"   URL  : http://0.0.0.0:{FASTAPI_PORT}")
    print(f"   Docs : http://localhost:{FASTAPI_PORT}/docs")
    print("=" * 60)
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=FASTAPI_PORT,
        reload=True,
        log_level="info",
    )
