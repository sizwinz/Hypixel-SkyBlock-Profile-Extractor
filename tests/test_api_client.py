import pytest
import responses

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


def test_client_repr_safe():
    from api_client import HypixelAPIClient

    raw_key = "12345678-1234-1234-1234-123456789abc"
    client = HypixelAPIClient(api_key=raw_key)

    repr_str = repr(client)
    assert repr_str == "<HypixelAPIClient authenticated=True>"
    assert raw_key not in repr_str

    unauth_client = HypixelAPIClient()
    assert repr(unauth_client) == "<HypixelAPIClient authenticated=False>"


@responses.activate
def test_get_player_uuid_success():
    from api_client import HypixelAPIClient

    client = HypixelAPIClient()
    responses.add(
        responses.GET,
        "https://api.mojang.com/users/profiles/minecraft/Technoblade",
        json={"name": "Technoblade", "id": "b876ec32e396476ba1158438d83c67d4"},
        status=200,
    )

    dashed_uuid, raw_uuid = client.get_player_uuid("Technoblade")
    assert raw_uuid == "b876ec32e396476ba1158438d83c67d4"
    assert dashed_uuid == "b876ec32-e396-476b-a115-8438d83c67d4"
