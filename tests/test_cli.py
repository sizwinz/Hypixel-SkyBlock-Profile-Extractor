import pytest
import responses
from pathlib import Path

def test_cli_helpers_raise_exceptions_without_sys_exit():
    import extract_profile
    from skyblock_extractor.api_client import PlayerNotFoundError

    # Mojang 404 should raise PlayerNotFoundError, NOT call sys.exit
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            "https://api.mojang.com/users/profiles/minecraft/NonExistent99",
            status=404,
        )
        with pytest.raises(PlayerNotFoundError):
            extract_profile.get_player_uuid("NonExistent99")

def test_cli_key_resolution_from_env(monkeypatch):
    import extract_profile

    monkeypatch.setenv("HYPIXEL_API_KEY", "test-env-key-12345678-1234-1234-1234")
    key = extract_profile.get_api_key(silent=True)
    assert key == "test-env-key-12345678-1234-1234-1234"
