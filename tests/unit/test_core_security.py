import pytest
from backend.app.core.security import hash_password, verify_password

pytestmark = pytest.mark.unit


def test_hash_password_produces_verifiable_hash() -> None:
    raw_value = "strong_secret_123"
    encoded_hash = hash_password(raw_value)

    assert encoded_hash != raw_value
    assert verify_password(raw_value, encoded_hash)


def test_verify_password_rejects_invalid_password() -> None:
    encoded_hash = hash_password("actual_secret_value")

    assert not verify_password("wrong_secret_value", encoded_hash)


def test_verify_password_rejects_malformed_hash() -> None:
    assert not verify_password("any_secret", "malformed-hash-value")
