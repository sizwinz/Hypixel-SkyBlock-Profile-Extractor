from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_hosted_mode_omits_api_key_input(monkeypatch):
    monkeypatch.setenv("STREAMLIT_HOSTED", "true")
    monkeypatch.delenv("HYPIXEL_API_KEY", raising=False)

    app = AppTest.from_file(APP_PATH, default_timeout=15)
    app.run()

    # Under hosted mode, personal API key input must NOT exist
    labels = [t.label for t in app.text_input]
    assert "Hypixel API Key" not in labels
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





