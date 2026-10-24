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


def test_extract_data_uses_fresh_extracted_profile_for_analysis(monkeypatch, tmp_path):
    import extract_profile
    from skyblock_extractor.extractor import ExtractionResult
    from skyblock_extractor.analysis import ProfileAnalyzer

    analyzed_profile_data = {}

    def mock_analyze(self, player_uuid, profile_data, auxiliary_data=None):
        nonlocal analyzed_profile_data
        analyzed_profile_data = profile_data
        return {
            "disclaimer": "test",
            "skills": {},
            "skill_average": 0.0,
            "slayers": {},
            "dungeons": {},
            "recommendations": [],
        }

    monkeypatch.setattr(ProfileAnalyzer, "analyze", mock_analyze)

    fresh_profile_payload = {
        "profile_id": "test-pid",
        "fresh_marker": True,
        "members": {},
    }

    def mock_extract(self, player_uuid, profile, categories=None):
        return {
            "profile": ExtractionResult(
                category="profile",
                filename="complete_profile.json",
                description="Profile",
                status="success",
                data=fresh_profile_payload,
            )
        }

    from skyblock_extractor.extractor import ProfileExtractor
    monkeypatch.setattr(ProfileExtractor, "extract", mock_extract)

    stale_profile = {
        "profile_id": "test-pid",
        "name": "Apple",
        "game_mode": "normal",
        "data": {"stale_marker": True},
    }

    out_dir, count = extract_profile.extract_data(
        uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile=stale_profile,
        api_key="mock-key-12345678-1234-1234-1234",
        username="Tester",
        custom_out_dir=tmp_path,
        create_zip=False,
    )

    assert analyzed_profile_data.get("fresh_marker") is True
    assert "stale_marker" not in analyzed_profile_data


def test_entry_points_include_src_in_sys_path():
    import subprocess
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        "-c",
        "import sys, pathlib; p = str(pathlib.Path('src').resolve()); sys.path = [x for x in sys.path if x != p]; assert p not in sys.path; import extract_profile; assert p in sys.path",
    ]
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    assert result.returncode == 0, f"Subprocess failed:\n{result.stderr}"


def test_cli_main_exits_nonzero_on_complete_extraction_failure(monkeypatch, tmp_path):
    import sys
    from skyblock_extractor import cli

    monkeypatch.setattr(cli, "get_api_key", lambda **kwargs: "mock-key-12345678-1234-1234-1234")
    monkeypatch.setattr(cli, "get_player_uuid", lambda user: ("uuid-1234", "uuid1234"))
    monkeypatch.setattr(cli, "get_profiles", lambda uuid, key: [{"profile_id": "pid-1", "name": "Apple", "game_mode": "normal"}])
    monkeypatch.setattr(cli, "select_profile", lambda profiles, **kwargs: profiles[0])
    # extract_data returns 0 successful extractions
    monkeypatch.setattr(cli, "extract_data", lambda **kwargs: (tmp_path, 0))

    monkeypatch.setattr(sys, "argv", ["extract_profile.py", "Tester", "-s"])

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code != 0





