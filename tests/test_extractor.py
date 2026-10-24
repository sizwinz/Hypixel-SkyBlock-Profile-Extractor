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
