"""
DN Agentic KYC Intelligence Platform — Frontend entry point.

Run from the kyc_platform/ directory:
    cd kyc_platform
    python run_frontend.py
"""

import sys
import os
import subprocess

# Ensure kyc_platform/ is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import STREAMLIT_PORT

if __name__ == "__main__":
    print("=" * 60)
    print("🖥️  DN Agentic KYC Intelligence Platform — Frontend")
    print(f"   URL : http://localhost:{STREAMLIT_PORT}")
    print("=" * 60)
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(os.path.dirname(__file__), "frontend", "app.py"),
        "--server.port", str(STREAMLIT_PORT),
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.address", "0.0.0.0",
    ])
