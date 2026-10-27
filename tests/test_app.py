from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_profile_results_live_in_their_own_top_level_tab():
    from skyblock_extractor.extractor import ExtractionResult

    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    results_tabs = [tab for tab in app.tabs if "Profile results" in tab.label]
    assert len(results_tabs) == 1
    assert any("Extract a profile" in message.value for message in results_tabs[0].info)

    app.session_state.extraction_results = {
        "profile": ExtractionResult("profile", "complete_profile.json", "Profile", "success", data={})
    }
    app.session_state.summary = {
        "skill_average": 25,
        "progression_priorities": ["Raise your farming skill."],
    }
    app.run()

    results = next(tab for tab in app.tabs if "Profile results" in tab.label)
    lookup = next(tab for tab in app.tabs if "Player Lookup" in tab.label or "Player Profile Backup" in tab.label)
    assert lookup.metric[0].value == "25"
    # Older AppTest versions include the parent tab in this collection.
    assert [tab.label for tab in results.tabs if tab.label != results.label] == [
        ":material/network_check: Endpoint Status",
        ":material/code: File Previews",
    ]
    assert any(item.value == "Raise your farming skill." for item in lookup.markdown)
    assert not app.exception


def test_page_uses_native_spacing_without_compact_css_overrides():
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()

    assert not app.exception
    assert not any("<style>" in element.value for element in app.get("html")), (
        "Native typography and layout spacing must not be compressed by injected CSS"
    )


def test_subheader_compatibility_without_icon_kwarg(monkeypatch):
    import streamlit as st

    original_subheader = st.subheader

    def mock_subheader(body, *args, **kwargs):
        if "icon" in kwargs:
            raise TypeError("subheader() got an unexpected keyword argument 'icon'")
        return original_subheader(body, *args, **kwargs)

    monkeypatch.setattr(st, "subheader", mock_subheader)
    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    assert not app.exception


def test_player_lookup_batches_username_until_submit(monkeypatch):
    from unittest.mock import Mock
    from skyblock_extractor.api_client import HypixelAPIClient

    monkeypatch.setenv("HYPIXEL_API_KEY", "test-key")
    resolve_player = Mock(return_value=("player-uuid", "playeruuid"))
    fetch_profiles = Mock(return_value=[])
    monkeypatch.setattr(HypixelAPIClient, "get_player_uuid", resolve_player)
    monkeypatch.setattr(HypixelAPIClient, "get_skyblock_profiles", fetch_profiles)

    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    lookup = app.get("form")
    assert len(lookup) == 1, "Player lookup should be one submit-based form"
    username = lookup[0].text_input[0]
    username.set_value("  TestPlayer  ")
    resolve_player.assert_not_called()
    lookup[0].button[0].click().run()

    resolve_player.assert_called_once_with("TestPlayer")
    fetch_profiles.assert_called_once_with("player-uuid")
    assert not app.exception


def test_app_hosted_mode_allows_api_key_input_when_env_key_absent(monkeypatch):
    monkeypatch.setenv("STREAMLIT_HOSTED", "true")
    monkeypatch.delenv("HYPIXEL_API_KEY", raising=False)

    app = AppTest.from_file(APP_PATH, default_timeout=15)
    app.run()

    # When env key is absent or not working, people can put their key from the UI
    labels = [t.label for t in app.text_input]
    assert any("API Key" in label for label in labels)
    assert not app.exception


def test_player_lookup_omits_redundant_cloud_banner_in_hosted_mode(monkeypatch):
    monkeypatch.setenv("STREAMLIT_HOSTED", "true")
    monkeypatch.delenv("HYPIXEL_API_KEY", raising=False)

    app = AppTest.from_file(APP_PATH, default_timeout=15).run()
    player_tab = next(tab for tab in app.tabs if "Player Lookup" in tab.label)
    assert not any("Streamlit Community Cloud Deployment" in info.value for info in player_tab.info)
    assert not app.exception


def test_target_profile_card_metadata_omits_duplicate_profile_name():
    app = AppTest.from_file(APP_PATH, default_timeout=15)
    app.session_state.profiles = [
        {
            "id": "abc1234567890",
            "name": "Tomato",
            "game_mode": "normal",
            "last_save": 1700000000000,
            "selected": True,
        }
    ]
    app.run()

    captions = [c.value for c in app.caption]
    assert any("**Mode:** Normal" in c for c in captions)
    assert any("**Profile ID:**" in c for c in captions)
    assert not any("**Profile Name:**" in c for c in captions)
    assert not app.exception


def test_app_desktop_mode_includes_api_key_input(monkeypatch):
    for var in [
        "HYPIXEL_API_KEY", "STREAMLIT_HOSTED", "MULTI_USER", "SERVER_NAME",
        "RENDER", "DYNO", "SPACE_ID", "FLY_APP_NAME", "RAILWAY_ENVIRONMENT",
        "KUBERNETES_SERVICE_HOST", "STREAMLIT_SERVER_HEADLESS", "STREAMLIT_SHARING_MODE",
    ]:
        monkeypatch.delenv(var, raising=False)

    app = AppTest.from_file(APP_PATH, default_timeout=15)
    app.run()

    labels = [t.label for t in app.text_input]
    assert "Hypixel API Key" in labels
    assert not app.exception


def test_app_renders_public_resources_tab():
    app = AppTest.from_file(APP_PATH, default_timeout=15)
    app.run()

    tab_labels = [tab.label for tab in app.tabs]
    assert any("Public Game Resources" in label for label in tab_labels)


def test_app_public_resources_extraction_trigger():
    import responses

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/items",
            json={"success": True, "items": [{"id": "HYPERION"}]},
            status=200,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/skills",
            json={"success": True, "skills": {}},
            status=200,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/collections",
            json={"success": True, "collections": {}},
            status=200,
        )

        app = AppTest.from_file(APP_PATH, default_timeout=15)
        app.run()

        pub_btn = None
        for b in app.button:
            if b.label == "Extract Public Resources":
                pub_btn = b
                break

        assert pub_btn is not None
        pub_btn.click().run()

        import zipfile
        zip_buffer = app.session_state.public_zip_buffer
        assert zip_buffer is not None
        with zipfile.ZipFile(zip_buffer) as archive:
            namelist = archive.namelist()
            assert "skyblock_items.json" in namelist
            assert "skyblock_skills_resource.json" in namelist
            assert "skyblock_collections_resource.json" in namelist
            assert "extraction_manifest.json" in namelist

        assert not app.exception


def test_app_public_resources_handles_total_failure():
    import responses

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/items",
            status=500,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/skills",
            status=500,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/collections",
            status=500,
        )

        app = AppTest.from_file(APP_PATH, default_timeout=15)
        app.run()

        pub_btn = None
        for b in app.button:
            if b.label == "Extract Public Resources":
                pub_btn = b
                break

        assert pub_btn is not None
        pub_btn.click().run()

        assert app.session_state.public_outcome["status"] == "complete_failure"
        assert app.session_state.public_zip_buffer is None
        assert not app.exception


def test_app_public_resources_handles_partial_success():
    import responses
    import zipfile

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/items",
            json={"success": True, "items": [{"id": "ITEM_1"}]},
            status=200,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/skills",
            status=500,
        )
        rsps.add(
            responses.GET,
            "https://api.hypixel.net/v2/resources/skyblock/collections",
            json={"success": True, "collections": {}},
            status=200,
        )

        app = AppTest.from_file(APP_PATH, default_timeout=15)
        app.run()

        pub_btn = None
        for b in app.button:
            if b.label == "Extract Public Resources":
                pub_btn = b
                break

        assert pub_btn is not None
        pub_btn.click().run()

        assert app.session_state.public_outcome["status"] == "partial_success"
        zip_buf = app.session_state.public_zip_buffer
        assert zip_buf is not None
        with zipfile.ZipFile(zip_buf) as archive:
            namelist = archive.namelist()
            assert "skyblock_items.json" in namelist
            assert "skyblock_collections_resource.json" in namelist
            assert "skyblock_skills_resource.json" not in namelist
        assert not app.exception





