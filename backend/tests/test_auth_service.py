import os

import pytest

from services.auth_service import AuthService


def test_verify_token_handles_invalid_input(tmp_path):
    db_path = tmp_path / "auth.db"
    service = AuthService(db_path=str(db_path))

    token = service.create_access_token("user-id", "test@example.com")
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "user-id"

    assert service.verify_token("not-a-real-token") is None


def test_register_user_prevents_duplicate_emails(tmp_path):
    db_path = tmp_path / "auth.db"
    service = AuthService(db_path=str(db_path))

    first = service.register_user("dup@example.com", "First", "secret")
    assert first is not None

    second = service.register_user("dup@example.com", "Second", "secret")
    assert second is None
