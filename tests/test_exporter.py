import json
import zipfile
import io
from pathlib import Path
import pytest

def test_profile_exporter_manifest_and_zip(tmp_path: Path):
    from exporter import ProfileExporter
    from extractor import ExtractionResult

    results = {
        "profile": ExtractionResult(
            category="profile",
            filename="complete_profile.json",
            description="Complete Profile",
            status="success",
            data={"cute_name": "Tomato", "members": {}},
        ),
        "guild": ExtractionResult(
            category="guild",
            filename="guild_data.json",
            description="Guild Info",
            status="failed",
            error_message="Player not in guild",
        ),
    }

    summary_data = {
        "profile_name": "Tomato",
        "game_mode": "normal",
        "skill_average": 28.5,
    }

    exporter = ProfileExporter(
        username="Technoblade",
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile_name="Tomato",
        profile_id="test-p123",
        results=results,
        summary=summary_data,
        base_dir=tmp_path,
    )

    out_dir = exporter.export_to_directory()

    assert out_dir.exists()
    assert (out_dir / "complete_profile.json").exists()
    assert (out_dir / "profile_summary.json").exists()
    assert (out_dir / "extraction_manifest.json").exists()
    assert (out_dir / "README.txt").exists()

    # Verify manifest structure and SHA256 checksum
    manifest = json.loads((out_dir / "extraction_manifest.json").read_text(encoding="utf-8"))
    assert manifest["username"] == "Technoblade"
    assert manifest["summary"]["successful"] == 1
    assert manifest["summary"]["failed"] == 1
    assert "complete_profile.json" in manifest["files"]
    assert "sha256" in manifest["files"]["complete_profile.json"]

    # Verify in-memory zip generation
    zip_buffer = exporter.build_zip_in_memory()
    assert isinstance(zip_buffer, io.BytesIO)
    with zipfile.ZipFile(zip_buffer, "r") as zf:
        namelist = zf.namelist()
        assert "complete_profile.json" in namelist
        assert "profile_summary.json" in namelist
        assert "extraction_manifest.json" in namelist
