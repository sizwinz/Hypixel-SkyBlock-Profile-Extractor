import pytest
import responses
from skyblock_extractor.extractor import ProfileExtractor
from skyblock_extractor.api_client import HypixelAPIClient

@responses.activate
def test_extractor_resilience_and_progress():
    client = HypixelAPIClient(api_key="mock-key-12345678-1234-1234-1234")

    # Mock endpoints
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/profile?profile=test-p1",
        json={"success": True, "profile": {"profile_id": "test-p1", "members": {}}},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/player?uuid=b876ec32-e396-476b-a115-8438d83c67d4",
        json={"success": True, "player": {"displayname": "Tester"}},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/guild?player=b876ec32-e396-476b-a115-8438d83c67d4",
        json={"success": False, "cause": "Player is not in a guild"},
        status=200,
    )

    progress_events = []
    def on_progress(step: int, total: int, category: str, status: str):
        progress_events.append((step, total, category, status))

    extractor = ProfileExtractor(client=client, progress_callback=on_progress)
    categories = ["profile", "player", "guild"]

    selected_profile = {
        "profile_id": "test-p1",
        "name": "Apple",
        "game_mode": "normal",
        "data": {"profile_id": "test-p1"},
    }

    results = extractor.extract(
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile=selected_profile,
        categories=categories,
    )

    assert len(results) == 3
    assert results["profile"].status == "success"
    assert results["profile"].data["profile_id"] == "test-p1"
    assert results["player"].status == "success"

    # Guild failed, but did not crash the extraction
    assert results["guild"].status == "failed"
    assert "Player is not in a guild" in results["guild"].error_message

    assert len(progress_events) == 3
    assert progress_events[-1][0] == 3
    assert progress_events[-1][1] == 3


@responses.activate
def test_extractor_items_endpoint_keyless():
    client = HypixelAPIClient(api_key="mock-key-12345678-1234-1234-1234")
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/items",
        json={"success": True, "items": [{"id": "ASPECT_OF_THE_JERRY", "name": "Aspect of the Jerry"}]},
        status=200,
    )

    extractor = ProfileExtractor(client=client)
    selected_profile = {"profile_id": "test-p1"}

    results = extractor.extract(
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile=selected_profile,
        categories=["items"],
    )

    assert "items" in results
    assert results["items"].status == "success"
    assert results["items"].filename == "skyblock_items.json"
    assert results["items"].data["items"][0]["id"] == "ASPECT_OF_THE_JERRY"

    # Verify that the HTTP request was made to resources/skyblock/items without API-Key header
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.url == "https://api.hypixel.net/v2/resources/skyblock/items"
    assert "API-Key" not in call.request.headers

