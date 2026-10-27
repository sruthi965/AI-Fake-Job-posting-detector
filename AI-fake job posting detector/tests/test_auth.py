from app.core.security import create_access_token, decode_access_token, hash_password, limiter, verify_password
from app.services import auth_service


def test_password_hash_roundtrip():
    stored = hash_password("correct horse battery")
    assert stored != "correct horse battery"
    assert verify_password("correct horse battery", stored)
    assert not verify_password("wrong password", stored)
    assert not verify_password("anything", "not-a-valid-hash")


def test_hashes_are_salted():
    assert hash_password("same-password") != hash_password("same-password")


def test_token_roundtrip_and_tampering():
    token = create_access_token(42)
    assert decode_access_token(token) == 42
    assert decode_access_token(token + "x") is None
    assert decode_access_token("garbage") is None


def test_token_signed_with_other_key_is_rejected(monkeypatch):
    token = create_access_token(7)
    monkeypatch.setenv("SECRET_KEY", "a-completely-different-secret-key-9876543210")
    assert decode_access_token(token) is None


def test_register_and_login():
    from app.database.connection import init_db

    init_db()
    user, token = auth_service.register_user("Asha Rao", "asha@example.com", "s3cret-pass")
    assert user["email"] == "asha@example.com" and "password_hash" not in user
    assert decode_access_token(token) == user["id"]
    logged_in, _ = auth_service.login_user("asha@example.com", "s3cret-pass")
    assert logged_in["id"] == user["id"]


def test_duplicate_email_and_bad_login():
    import pytest
    from app.database.connection import init_db

    init_db()
    auth_service.register_user("A One", "dup@example.com", "s3cret-pass")
    with pytest.raises(auth_service.ServiceError) as dup:
        auth_service.register_user("A Two", "dup@example.com", "another-pass")
    assert dup.value.status_code == 409
    with pytest.raises(auth_service.ServiceError) as bad:
        auth_service.login_user("dup@example.com", "wrong-pass")
    assert bad.value.status_code == 401
    with pytest.raises(auth_service.ServiceError) as unknown:
        auth_service.login_user("nobody@example.com", "whatever")
    assert unknown.value.detail == bad.value.detail  # same message: no account enumeration


def test_rate_limiter_blocks_after_limit():
    assert all(limiter.allow("k", 3, 60) for _ in range(3))
    assert not limiter.allow("k", 3, 60)
    assert limiter.allow("other", 3, 60)
