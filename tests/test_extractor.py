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


def test_classify_extraction_outcome_states():
    from skyblock_extractor.extractor import ExtractionResult, classify_extraction_outcome

    r_success = ExtractionResult("p", "p.json", "desc", "success")
    r_failed = ExtractionResult("g", "g.json", "desc", "failed", error_message="Error")

    # Complete success
    outcome_all_ok = classify_extraction_outcome({"p": r_success})
    assert outcome_all_ok["status"] == "complete_success"
    assert outcome_all_ok["success_count"] == 1
    assert outcome_all_ok["total_count"] == 1

    # Partial success
    outcome_partial = classify_extraction_outcome({"p": r_success, "g": r_failed})
    assert outcome_partial["status"] == "partial_success"
    assert outcome_partial["success_count"] == 1
    assert outcome_partial["total_count"] == 2

    # Complete failure
    outcome_all_fail = classify_extraction_outcome({"g": r_failed})
    assert outcome_all_fail["status"] == "complete_failure"
    assert outcome_all_fail["success_count"] == 0
    assert outcome_all_fail["total_count"] == 1


@responses.activate
def test_extractor_profile_fallback_reports_provenance_and_fallback_status():
    from skyblock_extractor.extractor import ProfileExtractor, classify_extraction_outcome
    from skyblock_extractor.api_client import HypixelAPIClient

    client = HypixelAPIClient(api_key="mock-key-12345678-1234-1234-1234", max_retries=0)
    # Mock fresh profile request to fail with 500
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/skyblock/profile?profile=test-p1",
        status=500,
    )

    extractor = ProfileExtractor(client=client)
    selected_profile = {
        "profile_id": "test-p1",
        "name": "Apple",
        "game_mode": "normal",
        "data": {"profile_id": "test-p1", "members": {}},
    }

    results = extractor.extract(
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile=selected_profile,
        categories=["profile"],
    )

    assert "profile" in results
    prof_res = results["profile"]
    assert prof_res.status == "fallback"
    assert prof_res.is_fallback is True
    assert prof_res.source == "discovery_snapshot"
    assert prof_res.error_message is not None
    assert "fell back to discovery snapshot" in prof_res.error_message

    # Classification should recognize fallback as partial_success, not complete_success
    outcome = classify_extraction_outcome(results)
    assert outcome["status"] == "partial_success"
    assert outcome["fallback_count"] == 1
    assert outcome["success_count"] == 0


@responses.activate
def test_extractor_unauthenticated_public_resource_endpoints():
    from skyblock_extractor.extractor import ProfileExtractor
    from skyblock_extractor.api_client import HypixelAPIClient

    # Completely unauthenticated client (no API key)
    client = HypixelAPIClient(api_key=None)

    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/items",
        json={"success": True, "items": [{"id": "ITEM_1"}]},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/skills",
        json={"success": True, "skills": {"COMBAT": {"maxLevel": 60}}},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/collections",
        json={"success": True, "collections": {"FARMING": {}}},
        status=200,
    )

    extractor = ProfileExtractor(client=client)
    results = extractor.extract(
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile={"profile_id": "test-p1"},
        categories=["items", "skills_resource", "collections_resource"],
    )

    assert results["items"].status == "success"
    assert results["skills_resource"].status == "success"
    assert results["collections_resource"].status == "success"

    # All calls must be keyless
    for call in responses.calls:
        assert "API-Key" not in call.request.headers


@responses.activate
def test_extractor_extract_public_resources_independent_of_player():
    from skyblock_extractor.extractor import ProfileExtractor
    from skyblock_extractor.api_client import HypixelAPIClient

    client = HypixelAPIClient(api_key=None)

    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/items",
        json={"success": True, "items": [{"id": "HYPERION"}]},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.hypixel.net/v2/resources/skyblock/skills",
        json={"success": True, "skills": {"MINING": {"maxLevel": 60}}},
        status=200,
    )

    extractor = ProfileExtractor(client=client)
    # Genuinely independent call without player_uuid or profile
    results = extractor.extract_public_resources(categories=["items", "skills_resource"])

    assert "items" in results
    assert results["items"].status == "success"
    assert results["items"].filename == "skyblock_items.json"
    assert results["items"].data == {"success": True, "items": [{"id": "HYPERION"}]}

    assert "skills_resource" in results
    assert results["skills_resource"].status == "success"
    assert results["skills_resource"].filename == "skyblock_skills_resource.json"

    for call in responses.calls:
        assert "API-Key" not in call.request.headers





