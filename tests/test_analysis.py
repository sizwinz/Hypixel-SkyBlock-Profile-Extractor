import pytest

def test_profile_analyzer_progression_and_disclaimer():
    from analysis import ProfileAnalyzer

    player_uuid = "b876ec32-e396-476b-a115-8438d83c67d4"
    profile_data = {
        "profile_id": "test-prof-123",
        "cute_name": "Tomato",
        "game_mode": "ironman",
        "members": {
            "b876ec32e396476ba1158438d83c67d4": {
                "experience_skill_combat": 600000,   # Level ~24
                "experience_skill_mining": 1200000,  # Level ~27
                "slayer": {
                    "slayer_bosses": {
                        "zombie": {"xp": 50000},
                        "spider": {"xp": 10000},
                        "wolf": {"xp": 1500},
                    }
                },
                "dungeons": {
                    "dungeon_types": {
                        "catacombs": {
                            "experience": 250000,
                        }
                    },
                    "selected_dungeon_class": "mage",
                },
            }
        },
    }

    auxiliary_data = {
        "garden": {
            "garden": {
                "level": 9,
                "completed_visitors": 45,
            }
        }
    }

    analyzer = ProfileAnalyzer()
    summary = analyzer.analyze(
        player_uuid=player_uuid,
        profile_data=profile_data,
        auxiliary_data=auxiliary_data,
    )

    # Core profile info
    assert summary["profile_name"] == "Tomato"
    assert summary["game_mode"] == "ironman"

    # Skills analysis
    assert "combat" in summary["skills"]
    assert summary["skills"]["combat"]["level"] == 20
    assert summary["skill_average"] > 0

    # Slayers
    assert summary["slayer"]["zombie"]["xp"] == 50000

    # Dungeons
    assert summary["dungeons"]["class"] == "mage"
    assert summary["dungeons"]["catacombs_level"] > 10

    # Priorities & Disclaimers
    assert len(summary["progression_priorities"]) >= 1
    assert "Bazaar prices" in summary["disclaimers"]["net_worth"]
    assert "in-game API privacy" in summary["disclaimers"]["api_privacy"]
