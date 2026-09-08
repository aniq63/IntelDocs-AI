import re
import pytest

from utils.authentication import (
    hash_password,
    verify_password,
    generate_session_token,
)


class TestHashPassword:

    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_different_hashes_for_same_input(self):
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        # bcrypt uses random salts so hashes differ
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self):
        result = hash_password("test")
        assert result.startswith("$2")

    def test_hash_is_not_plaintext(self):
        result = hash_password("secret123")
        assert "secret123" not in result


class TestVerifyPassword:

    def test_correct_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_password_roundtrip(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True

    def test_special_characters(self):
        hashed = hash_password("!@#$%^&*()_+{}|:<>?")
        assert verify_password("!@#$%^&*()_+{}|:<>?", hashed) is True

    def test_unicode_password(self):
        hashed = hash_password("p\u00e4\u00e4ssw\u00f6rd")
        assert verify_password("p\u00e4\u00e4ssw\u00f6rd", hashed) is True


class TestGenerateSessionToken:

    def test_returns_string(self):
        token = generate_session_token()
        assert isinstance(token, str)

    def test_hex_format(self):
        token = generate_session_token()
        assert re.fullmatch(r"[0-9a-f]+", token)

    def test_default_uuid4_length(self):
        token = generate_session_token()
        # uuid4 hex is 32 chars
        assert len(token) == 32

    def test_unique_tokens(self):
        tokens = {generate_session_token() for _ in range(100)}
        assert len(tokens) == 100
