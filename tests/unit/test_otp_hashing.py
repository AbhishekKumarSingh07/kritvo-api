"""The plain OTP code is never stored or returned — only its HMAC (LLD 12.1, ADR-0008)."""

from kritvo.modules.identity import schemas, security


def test_generated_code_is_six_digits() -> None:
    for _ in range(50):
        code = security.generate_otp_code()
        assert len(code) == 6
        assert code.isdigit()


def test_hash_never_equals_the_code() -> None:
    code = security.generate_otp_code()
    digest = security.hash_otp_code(code, "a-key")
    assert digest != code.encode()
    assert code.encode() not in digest


def test_hash_is_deterministic_for_verification() -> None:
    code = "123456"
    assert security.hash_otp_code(code, "a-key") == security.hash_otp_code(code, "a-key")


def test_different_codes_hash_differently() -> None:
    assert security.hash_otp_code("111111", "a-key") != security.hash_otp_code("222222", "a-key")


def test_different_keys_hash_the_same_code_differently() -> None:
    """A leaked otp_codes table alone (without the app's key) does not reveal codes."""
    assert security.hash_otp_code("123456", "key-a") != security.hash_otp_code("123456", "key-b")


def test_otp_request_response_has_no_code_field() -> None:
    fields = schemas.OtpRequestOut.model_fields
    assert "code" not in fields
    assert set(fields) == {"ok"}


def test_refresh_token_is_high_entropy_and_hash_differs() -> None:
    token = security.generate_refresh_token()
    assert len(token) >= 32
    digest = security.hash_refresh_token(token)
    assert digest != token.encode()
    assert token.encode() not in digest
