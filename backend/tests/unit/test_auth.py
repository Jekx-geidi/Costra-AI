import pytest
from app.auth.jwt import hash_password, verify_password, create_access_token, decode_token


def test_hash_and_verify_password():
    pw = "correct-horse-battery-staple"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token():
    token = create_access_token(subject="test@geidi.com", role="billing_admin")
    payload = decode_token(token)
    assert payload["sub"] == "test@geidi.com"
    assert payload["role"] == "billing_admin"


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_token("not.a.valid.jwt")


def test_token_contains_no_secrets():
    import base64, json
    token = create_access_token(subject="user@geidi.com", role="viewer")
    parts = token.split(".")
    padding = "=" * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(parts[1] + padding))
    assert "password" not in payload
    assert "api_key" not in payload
    assert "secret" not in payload
