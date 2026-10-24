import pytest

def test_normalize_profiles_dashed_and_undashed_uuid():
    from profile_service import normalize_profiles

    raw_profiles = [
        {
            "profile_id": "profile-alpha",
            "cute_name": "Tomato",
            "game_mode": "ironman",
            "selected": True,
            "members": {
                # Undashed UUID format
                "b876ec32e396476ba1158438d83c67d4": {
                    "last_save": 1700000000000,
                    "experience_skill_combat": 50000,
                }
            },
        },
        {
            "profile_id": "profile-beta",
            "cute_name": "Cucumber",
            "members": {
                # Dashed UUID format
                "b876ec32-e396-476b-a115-8438d83c67d4": {
                    "last_save": 1710000000000,
                }
            },
        },
        {
            "profile_id": "profile-gamma",
            "cute_name": "Peach",
            # Player not in members
            "members": {},
        },
    ]

    player_uuid = "b876ec32-e396-476b-a115-8438d83c67d4"
    normalized = normalize_profiles(raw_profiles, player_uuid)

    assert len(normalized) == 3
    # Sorted by last_save descending (Cucumber first with 1710000000000, then Tomato, then Peach)
    assert normalized[0]["profile_id"] == "profile-beta"
    assert normalized[0]["name"] == "Cucumber"
    assert normalized[0]["game_mode"] == "normal"
    assert normalized[0]["last_save"] == 1710000000000

    assert normalized[1]["profile_id"] == "profile-alpha"
    assert normalized[1]["name"] == "Tomato"
    assert normalized[1]["game_mode"] == "ironman"
    assert normalized[1]["last_save"] == 1700000000000

    assert normalized[2]["profile_id"] == "profile-gamma"
    assert normalized[2]["last_save"] == 0


def test_select_profile_silent_and_by_name():
    from profile_service import select_profile
    from api_client import ProfileNotFoundError

    profiles = [
        {"profile_id": "1", "name": "Apple", "last_save": 500},
        {"profile_id": "2", "name": "Banana", "last_save": 200},
    ]

    # Select by name (case-insensitive)
    selected = select_profile(profiles, requested_name="banana")
    assert selected["profile_id"] == "2"

    # Silent auto-select most recent
    selected_silent = select_profile(profiles, silent=True)
    assert selected_silent["profile_id"] == "1"

    # Empty list raises error
    with pytest.raises(ProfileNotFoundError, match="No SkyBlock profiles found"):
        select_profile([])
