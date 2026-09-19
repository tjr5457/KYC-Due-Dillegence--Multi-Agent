import os

# URL of the FastAPI backend — override via env var when deploying
API_BASE = os.getenv("KYC_API_BASE", "http://localhost:8001")
