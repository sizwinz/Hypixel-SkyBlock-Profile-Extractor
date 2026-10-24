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
