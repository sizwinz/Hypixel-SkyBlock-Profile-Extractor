import json
import zipfile
import io
from pathlib import Path
import pytest
from skyblock_extractor.exporter import ProfileExporter
from skyblock_extractor.extractor import ExtractionResult

def test_profile_exporter_manifest_and_zip(tmp_path: Path):

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


def test_profile_exporter_exports_fallback_data_with_provenance(tmp_path: Path):
    results = {
        "profile": ExtractionResult(
            category="profile",
            filename="complete_profile.json",
            description="Complete Profile Data",
            status="fallback",
            error_message="Fresh profile fetch failed (500 Server Error); fell back to discovery snapshot.",
            data={"profile_id": "fallback-pid-1", "members": {"test_uuid": {}}},
            is_fallback=True,
            source="discovery_snapshot",
        )
    }

    exporter = ProfileExporter(
        username="Technoblade",
        player_uuid="b876ec32-e396-476b-a115-8438d83c67d4",
        profile_name="Tomato",
        profile_id="fallback-pid-1",
        results=results,
        base_dir=tmp_path,
    )

    out_dir = exporter.export_to_directory()

    # The fallback profile JSON must be exported so the user still receives usable data
    assert (out_dir / "complete_profile.json").exists()
    exported_data = json.loads((out_dir / "complete_profile.json").read_text(encoding="utf-8"))
    assert exported_data["profile_id"] == "fallback-pid-1"

    # Manifest must record fallback provenance
    manifest = json.loads((out_dir / "extraction_manifest.json").read_text(encoding="utf-8"))
    assert manifest["summary"]["fallback"] == 1
    assert "complete_profile.json" in manifest["files"]
    prof_status = manifest["status_details"]["profile"]
    assert prof_status["status"] == "fallback"
    assert prof_status["is_fallback"] is True
    assert prof_status["source"] == "discovery_snapshot"

    # README report must indicate fallback tag
    readme = (out_dir / "README.txt").read_text(encoding="utf-8")
    assert "[FALLBACK]" in readme
    assert "complete_profile.json" in readme


def test_public_resource_exporter_bundle_and_zip(tmp_path: Path):
    from skyblock_extractor.exporter import PublicResourceExporter

    results = {
        "items": ExtractionResult(
            category="items",
            filename="skyblock_items.json",
            description="SkyBlock Items Schema",
            status="success",
            data={"success": True, "items": [{"id": "HYPERION"}]},
        ),
        "skills_resource": ExtractionResult(
            category="skills_resource",
            filename="skyblock_skills_resource.json",
            description="SkyBlock Skills Resource Schema",
            status="success",
            data={"success": True, "skills": {}},
        ),
    }

    exporter = PublicResourceExporter(results=results, base_dir=tmp_path)
    out_dir = exporter.export_to_directory()

    assert (out_dir / "skyblock_items.json").exists()
    assert (out_dir / "skyblock_skills_resource.json").exists()
    assert (out_dir / "extraction_manifest.json").exists()
    assert (out_dir / "README.txt").exists()

    manifest = json.loads((out_dir / "extraction_manifest.json").read_text(encoding="utf-8"))
    assert manifest["resource_type"] == "public_game_resources"
    assert manifest["summary"]["successful"] == 2
    assert "skyblock_items.json" in manifest["files"]

    readme = (out_dir / "README.txt").read_text(encoding="utf-8")
    assert "PUBLIC GAME RESOURCES REPORT" in readme

    zip_buf = exporter.build_zip_in_memory()
    with zipfile.ZipFile(zip_buf) as zf:
        namelist = zf.namelist()
        assert "skyblock_items.json" in namelist
        assert "skyblock_skills_resource.json" in namelist
        assert "extraction_manifest.json" in namelist


