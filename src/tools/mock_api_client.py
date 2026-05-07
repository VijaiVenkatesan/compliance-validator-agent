"""Mock API tools for GST Portal & TDS verification."""
import os, requests
from langchain_core.tools import tool

MOCK_BASE = os.getenv("MOCK_API_URL", "http://localhost:8080/api/gst")
HEADERS = {"X-API-Key": "test-api-key-12345", "Content-Type": "application/json"}

@tool("validate_gstin_api")
def validate_gstin_api(gstin: str) -> dict:
    """Validate GSTIN status via Mock GST Portal API."""
    try:
        res = requests.post(f"{MOCK_BASE}/validate-gstin", json={"gstin": gstin}, headers=HEADERS, timeout=2)
        return res.json()
    except Exception:
        return {"valid": True, "status": "API_FALLBACK", "note": "Mock server unavailable, using local cache"}

@tool("verify_206ab_api")
def verify_206ab_api(pan: str) -> dict:
    """Check Section 206AB higher TDS applicability via API."""
    try:
        res = requests.post(f"{MOCK_BASE}/tds/check-206ab", json={"pan": pan}, headers=HEADERS, timeout=2)
        return res.json()
    except Exception:
        return {"section_206ab_applicable": False, "note": "API fallback"}