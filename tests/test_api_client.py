import pytest
import responses

from skyblock_extractor.api_client import (
    SkyBlockExtractorError,
    AuthenticationError,
    RateLimitExceededError,
    PlayerNotFoundError,
    ProfileNotFoundError,
    APIResponseError,
    NetworkTimeoutError,
    HypixelAPIClient,
)

def test_custom_exception_hierarchy():
    assert issubclass(AuthenticationError, SkyBlockExtractorError)
    assert issubclass(RateLimitExceededError, SkyBlockExtractorError)
    assert issubclass(PlayerNotFoundError, SkyBlockExtractorError)
    assert issubclass(ProfileNotFoundError, SkyBlockExtractorError)
    assert issubclass(APIResponseError, SkyBlockExtractorError)
    assert issubclass(NetworkTimeoutError, SkyBlockExtractorError)


def test_api_key_redaction():
    raw_key = "12345678-1234-1234-1234-123456789abc"
    client = HypixelAPIClient(api_key=raw_key)

    text_with_key = f"Request to https://api.hypixel.net/v2/skyblock/profile?key={raw_key} failed"
    sanitized = client.redact_api_key(text_with_key)

    assert raw_key not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert client.redact_api_key(None) == ""


def test_client_repr_safe():
    raw_key = "12345678-1234-1234-1234-123456789abc"
    client = HypixelAPIClient(api_key=raw_key)

    repr_str = repr(client)
    assert repr_str == "<HypixelAPIClient authenticated=True>"
    assert raw_key not in repr_str

    unauth_client = HypixelAPIClient()
    assert repr(unauth_client) == "<HypixelAPIClient authenticated=False>"


@responses.activate
def test_get_player_uuid_success():
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


@responses.activate
def test_fetch_endpoint_429_retry_recovery(monkeypatch):
    client = HypixelAPIClient(api_key="valid-key-12345678-1234-1234-1234", max_retries=2)
    sleep_calls = []
    monkeypatch.setattr("time.sleep", lambda s: sleep_calls.append(s))

    # First call returns 429
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/garden",
        headers={"RateLimit-Reset": "1"},
        status=429,
    )
    # Second call succeeds
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/garden",
        json={"success": True, "garden": {"level": 10}},
        status=200,
    )

    data = client.fetch_endpoint("skyblock/garden")
    assert data["success"] is True
    assert data["garden"]["level"] == 10
    assert len(responses.calls) == 2
    assert len(sleep_calls) == 1
    assert sleep_calls[0] > 0



@responses.activate
def test_get_skyblock_profiles_and_profile():
    client = HypixelAPIClient(api_key="valid-key-12345678-1234-1234-1234")

    # Mock /v2/skyblock/profiles?uuid=...
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/profiles",
        json={
            "success": True,
            "profiles": [
                {"profile_id": "prof-1", "cute_name": "Apple"},
                {"profile_id": "prof-2", "cute_name": "Banana"},
            ],
        },
        status=200,
    )

    profiles = client.get_skyblock_profiles("b876ec32-e396-476b-a115-8438d83c67d4")
    assert len(profiles) == 2
    assert profiles[0]["cute_name"] == "Apple"

    # Mock /v2/skyblock/profile?profile=...
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/profile",
        json={
            "success": True,
            "profile": {"profile_id": "prof-1", "cute_name": "Apple", "members": {}},
        },
        status=200,
    )

    profile = client.get_skyblock_profile("prof-1")
    assert profile["profile_id"] == "prof-1"
    assert "members" in profile


@responses.activate
def test_fetch_endpoint_500_and_timeout():
    import requests
    client = HypixelAPIClient(api_key="valid-key-12345678-1234-1234-1234")

    # 500 Internal Server Error
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/news",
        status=500,
    )
    with pytest.raises(SkyBlockExtractorError, match="Hypixel API connection error"):
        client.fetch_endpoint("skyblock/news")

    # Network timeout
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/firesales",
        body=requests.exceptions.Timeout("Connection timed out"),
    )
    with pytest.raises(NetworkTimeoutError, match="timed out"):
        client.fetch_endpoint("skyblock/firesales")
