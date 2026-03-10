import pytest
from backend.app.core.exceptions import WeakPasswordError
from backend.app.core.security import hash_password, validate_password_policy, verify_password

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


def test_validate_password_policy_accepts_valid_password() -> None:
    validate_password_policy("valid_password1!")


def test_validate_password_policy_accepts_custom_limits() -> None:
    validate_password_policy("ab1!cd", min_length=6, max_length=10)


@pytest.mark.parametrize(
    ("password", "expected_message"),
    [
        ("a1!", "короче 8"),
        ("no_digits!", "цифру"),
        ("nospecial123", "спецсимвол"),
        ("has space1!", "пробелы"),
        ("a" * 25 + "1!", "длиннее 26"),
    ],
)
def test_validate_password_policy_rejects_invalid_password(
    password: str,
    expected_message: str,
) -> None:
    with pytest.raises(WeakPasswordError) as error_info:
        validate_password_policy(password)

    assert expected_message in error_info.value.message.lower()
