import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

from datetime import timedelta

import pytest
from jose import JWTError

from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)


class TestHashPassword:
    def test_returns_string(self):
        result = hash_password("mysecret")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_output_is_bcrypt_hash(self):
        result = hash_password("mysecret")
        assert result.startswith("$2b$")

    def test_different_salts_each_call(self):
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2

    def test_hash_is_not_plain_text(self):
        password = "plaintext"
        assert hash_password(password) != password


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        password = "correct_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_password_does_not_match_non_empty_hash(self):
        hashed = hash_password("nonempty")
        assert verify_password("", hashed) is False

    def test_verify_is_case_sensitive(self):
        hashed = hash_password("Password123")
        assert verify_password("password123", hashed) is False
        assert verify_password("PASSWORD123", hashed) is False


class TestCreateAccessToken:
    def test_returns_non_empty_string(self):
        token = create_access_token({"sub": "42"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_has_three_parts(self):
        token = create_access_token({"sub": "42"})
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_encodes_subject(self):
        token = create_access_token({"sub": "99"})
        payload = decode_token(token)
        assert payload["sub"] == "99"

    def test_custom_expiry_is_respected(self):
        token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(JWTError):
            decode_token(token)

    def test_default_expiry_is_set(self):
        token = create_access_token({"sub": "5"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_custom_data_preserved(self):
        token = create_access_token({"sub": "7", "role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"


class TestDecodeToken:
    def test_valid_token_returns_payload(self):
        token = create_access_token({"sub": "123"})
        payload = decode_token(token)
        assert payload["sub"] == "123"
        assert "exp" in payload

    def test_tampered_token_raises_jwt_error(self):
        token = create_access_token({"sub": "1"})
        parts = token.split(".")
        parts[-1] = parts[-1] + "tampered"
        bad_token = ".".join(parts)
        with pytest.raises(JWTError):
            decode_token(bad_token)

    def test_completely_invalid_string_raises_jwt_error(self):
        with pytest.raises(JWTError):
            decode_token("this.is.not.a.jwt")

    def test_expired_token_raises_jwt_error(self):
        expired_token = create_access_token(
            {"sub": "1"}, expires_delta=timedelta(seconds=-10)
        )
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_wrong_secret_raises_jwt_error(self):
        from jose import jwt as jose_jwt
        bad_token = jose_jwt.encode({"sub": "1"}, "WRONG_SECRET", algorithm="HS256")
        with pytest.raises(JWTError):
            decode_token(bad_token)
