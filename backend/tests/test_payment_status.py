import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend package modules (services, etc.) are importable
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from backend.app import app, payment_service

client = TestClient(app)

@pytest.mark.parametrize("endpoint", [
    "/api/v1/payment/status",
])
def test_payment_status_endpoint(endpoint):
    resp = client.get(endpoint)
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data


def test_payment_endpoints_unconfigured_guard(monkeypatch):
    """Ensure guarded endpoints return 503 when Stripe keys missing."""
    # Force unconfigured state by clearing env and reloading api key and webhook secret variables
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)

    # Since payment_service reads env at import time, we rely on is_configured() logic
    assert not payment_service.is_configured()

    # Register free user (should succeed without Stripe)
    # Use unique email each run to avoid collision with existing test data causing 400
    import uuid
    unique_email = f"ptest_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {"email": unique_email, "name": "Pay Test", "password": "pass123", "plan": "free"}
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 200
    token = r.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Portal session should fail with 503 due to unconfigured payments
    portal = client.post("/api/v1/payment/create-portal-session", headers=headers)
    assert portal.status_code == 503

    # Stripe webhook should fail with 503
    webhook = client.post("/api/v1/webhooks/stripe", content=b"{}", headers={"stripe-signature": "test"})
    assert webhook.status_code == 503


@pytest.mark.skipif(not payment_service.is_configured(), reason="Stripe not configured - skipping live payment tests")
def test_payment_portal_session_flow(monkeypatch):
    """If Stripe configured, attempt portal session creation path (requires a pro user)."""
    reg_payload = {"email": "protester@example.com", "name": "Pro Tester", "password": "pass123", "plan": "pro"}
    r = client.post("/api/v1/auth/register", json=reg_payload)
    assert r.status_code == 200
    data = r.json()
    # If configured, pro registration should return checkout session info OR token depending on flow
    assert "user" in data
    # Not asserting checkout fields because environment may not have real price IDs
