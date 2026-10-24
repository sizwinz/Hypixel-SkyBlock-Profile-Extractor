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


@responses.activate
def test_get_player_uuid_errors():
    from api_client import HypixelAPIClient, PlayerNotFoundError

    client = HypixelAPIClient()

    # Invalid username format
    with pytest.raises(PlayerNotFoundError, match="Invalid Minecraft username"):
        client.get_player_uuid("Invalid Name With Spaces!")

    # 404 Not Found from Mojang
    responses.add(
        responses.GET,
        "https://api.mojang.com/users/profiles/minecraft/GhostUser99999",
        status=404,
    )
    with pytest.raises(PlayerNotFoundError, match="does not exist"):
        client.get_player_uuid("GhostUser99999")


@responses.activate
def test_fetch_endpoint_header_auth():
    from api_client import HypixelAPIClient

    test_key = "12345678-1234-1234-1234-123456789abc"
    client = HypixelAPIClient(api_key=test_key)

    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/bazaar",
        json={"success": True, "products": {}},
        status=200,
    )

    data = client.fetch_endpoint("skyblock/bazaar")

    assert data.get("success") is True
    # Verify request headers
    assert len(responses.calls) == 1
    req = responses.calls[0].request
    assert req.headers.get("API-Key") == test_key
    assert "key=" not in req.url


@responses.activate
def test_fetch_endpoint_errors():
    from api_client import (
        HypixelAPIClient,
        AuthenticationError,
        RateLimitExceededError,
        APIResponseError,
    )

    client = HypixelAPIClient(api_key="bad-key-12345678-1234-1234-1234")

    # 403 Forbidden
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/profiles",
        status=403,
    )
    with pytest.raises(AuthenticationError, match="403 Forbidden"):
        client.fetch_endpoint("skyblock/profiles")

    # 429 Rate Limit
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/garden",
        headers={"RateLimit-Reset": "42"},
        status=429,
    )
    with pytest.raises(RateLimitExceededError, match="429 Too Many Requests.*reset in 42s"):
        client.fetch_endpoint("skyblock/garden")

    # Hypixel success=false response
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/museum",
        json={"success": False, "cause": "Profile not found"},
        status=200,
    )
    with pytest.raises(APIResponseError, match="Profile not found"):
        client.fetch_endpoint("skyblock/museum")
