import os
import sys
nfrom fastapi.testclient import TestClient

# Ensure backend package modules (services, etc.) are importable
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from backend.app import app

client = TestClient(app)


def test_root_and_health_and_ping():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json().get("service") == "EstimateGenie API"

    h = client.get("/health")
    assert h.status_code == 200
    assert "status" in h.json()

    p = client.get("/api/v1/ping")
    assert p.status_code == 200
    j = p.json()
    assert j.get("ok") is True


def test_quotes_requires_auth():
    # Send a tiny fake png as file to satisfy validation but expect 401 due to missing auth
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00IHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\xdac```\x00\x00\x00\x04\x00\x01\x0b\xe7\x02\x9a\x00\x00\x00\x00IEND\xaeB`\x82"
    files = {"file": ("tiny.png", png_bytes, "image/png")}
    resp = client.post("/v1/quotes", files=files)
    assert resp.status_code == 401

def test_api_config():
    r = client.get("/test-api-config.html")
    assert r.status_code == 200
    assert "API Configuration" in r.text
