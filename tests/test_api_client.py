import pytest

def test_custom_exception_hierarchy():
    from api_client import (
        SkyBlockExtractorError,
        AuthenticationError,
        RateLimitExceededError,
        PlayerNotFoundError,
        ProfileNotFoundError,
        APIResponseError,
        NetworkTimeoutError,
    )

    assert issubclass(AuthenticationError, SkyBlockExtractorError)
    assert issubclass(RateLimitExceededError, SkyBlockExtractorError)
    assert issubclass(PlayerNotFoundError, SkyBlockExtractorError)
    assert issubclass(ProfileNotFoundError, SkyBlockExtractorError)
    assert issubclass(APIResponseError, SkyBlockExtractorError)
    assert issubclass(NetworkTimeoutError, SkyBlockExtractorError)


def test_api_key_redaction():
    from api_client import HypixelAPIClient

    raw_key = "12345678-1234-1234-1234-123456789abc"
    client = HypixelAPIClient(api_key=raw_key)

    text_with_key = f"Request to https://api.hypixel.net/v2/skyblock/profile?key={raw_key} failed"
    sanitized = client.redact_api_key(text_with_key)

    assert raw_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert client.redact_api_key(None) == ""
