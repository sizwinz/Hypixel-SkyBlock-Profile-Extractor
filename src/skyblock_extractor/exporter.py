"""Serialization, extraction manifest creation, and ZIP export handling."""

import hashlib
import io
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from skyblock_extractor.extractor import ExtractionResult

VERSION = "2.1.0"


def calculate_sha256(data_bytes: bytes) -> str:
    """Calculate hex digest SHA-256 for bytes."""
    hasher = hashlib.sha256()
    hasher.update(data_bytes)
    return hasher.hexdigest()


class ProfileExporter:
    """Manages file writing, manifest calculation, and ZIP creation for exported profiles."""

    def __init__(
        self,
        username: str,
        player_uuid: str,
        profile_name: str,
        profile_id: str,
        results: Dict[str, ExtractionResult],
        summary: Optional[Dict[str, Any]] = None,
        base_dir: Optional[Path] = None,
        custom_out_dir: Optional[Path] = None,
    ):
        self.username = username
        self.player_uuid = player_uuid
        self.profile_name = profile_name
        self.profile_id = profile_id
        self.results = results
        self.summary = summary or {}
        self.base_dir = base_dir or Path.cwd()
        self.custom_out_dir = custom_out_dir
        self.timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

    @property
    def output_dir(self) -> Path:
        """Resolve final output directory."""
        if self.custom_out_dir:
            return self.custom_out_dir
        folder_name = f"SkyBlock_{self.username}_{self.profile_name}_{self.timestamp_str}"
        return self.base_dir / folder_name

    def build_export_payloads(self) -> Dict[str, bytes]:
        """Prepare in-memory dictionary of filename to serialized UTF-8 bytes."""
        payloads: Dict[str, bytes] = {}

        # 1. Extracted endpoint data (including usable fallback data)
        for cat, res in self.results.items():
            if res.status in ("success", "fallback") and res.data is not None:
                encoded = json.dumps(res.data, indent=2, ensure_ascii=False).encode("utf-8")
                payloads[res.filename] = encoded

        # 2. Profile Summary
        if self.summary:
            summary_bytes = json.dumps(self.summary, indent=2, ensure_ascii=False).encode("utf-8")
            payloads["profile_summary.json"] = summary_bytes

        # 3. Extraction Manifest
        file_entries: Dict[str, Dict[str, Any]] = {}
        for filename, data_bytes in payloads.items():
            file_entries[filename] = {
                "sha256": calculate_sha256(data_bytes),
                "size_bytes": len(data_bytes),
            }

        successful_count = sum(1 for r in self.results.values() if r.status == "success" and not r.is_fallback)
        fallback_count = sum(1 for r in self.results.values() if r.status == "fallback" or r.is_fallback)
        failed_count = sum(1 for r in self.results.values() if r.status == "failed")
        skipped_count = sum(1 for r in self.results.values() if r.status == "skipped")

        manifest = {
            "generator": f"SkyBlock-Profile-Extractor v{VERSION}",
            "generated_at": datetime.now().isoformat(),
            "username": self.username,
            "player_uuid": self.player_uuid,
            "profile_name": self.profile_name,
            "profile_id": self.profile_id,
            "summary": {
                "total_requested": len(self.results),
                "successful": successful_count,
                "fallback": fallback_count,
                "failed": failed_count,
                "skipped": skipped_count,
            },
            "status_details": {
                cat: {
                    "filename": r.filename,
                    "status": r.status,
                    "is_fallback": r.is_fallback,
                    "source": getattr(r, "source", "fresh"),
                    "error_message": r.error_message,
                }
                for cat, r in self.results.items()
            },
            "files": file_entries,
            "disclaimer": (
                "Data extracted via official Hypixel API v2. Not affiliated with or endorsed by Hypixel. "
                "Point-in-time snapshot created by direct user request."
            ),
        }

        manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
        payloads["extraction_manifest.json"] = manifest_bytes

        # 4. Human-readable README.txt
        completeness_info = f"{successful_count}/{len(self.results)} endpoints successfully extracted"
        if fallback_count:
            completeness_info += f" ({fallback_count} using discovery fallback)"

        readme_lines = [
            "HYPIXEL SKYBLOCK PROFILE EXTRACTION REPORT",
            "=" * 50,
            f"Generated:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Player:      {self.username}",
            f"UUID:        {self.player_uuid}",
            f"Profile:     {self.profile_name} ({self.profile_id})",
            f"Completeness:{completeness_info}",
            "",
            "EXTRACTION STATUS:",
            "-" * 50,
        ]
        for cat, r in self.results.items():
            status_tag = (
                "[OK]      " if r.status == "success" and not r.is_fallback
                else "[FALLBACK]" if r.status == "fallback" or r.is_fallback
                else "[FAILED]  " if r.status == "failed"
                else "[SKIP]    "
            )
            err_info = f" ({r.error_message})" if r.error_message else ""
            readme_lines.append(f"{status_tag} {r.filename:24} - {r.description}{err_info}")

        if self.summary:
            readme_lines.extend([
                "",
                "PROGRESSION HIGHLIGHTS:",
                "-" * 50,
                f"Skill Average: {self.summary.get('skill_average', 'N/A')}",
                f"Catacombs:     Level {self.summary.get('dungeons', {}).get('catacombs_level', 0)} ({self.summary.get('dungeons', {}).get('class', 'none')})",
            ])
            priorities = self.summary.get("progression_priorities", [])
            if priorities:
                readme_lines.append("\nSuggested Progression Priorities:")
                for p in priorities:
                    readme_lines.append(f" - {p}")

        readme_lines.extend([
            "",
            "NOTES & DISCLAIMERS:",
            "-" * 50,
            "1. 'complete_profile.json' contains all raw player member data.",
            "2. 'profile_summary.json' provides deterministic skill and progression calculations.",
            "3. 'extraction_manifest.json' contains SHA256 integrity checksums for all files.",
            "4. Bazaar prices reflect market snapshots and do not constitute an authoritative net worth.",
            "5. Extracted on-demand using official Hypixel API v2 without continuous player tracking.",
        ])

        payloads["README.txt"] = "\n".join(readme_lines).encode("utf-8")

        return payloads

    def export_to_directory(self) -> Path:
        """Write all generated payloads to the destination directory."""
        dir_path = self.output_dir
        dir_path.mkdir(parents=True, exist_ok=True)

        payloads = self.build_export_payloads()
        for filename, data_bytes in payloads.items():
            target_file = dir_path / filename
            target_file.write_bytes(data_bytes)

        return dir_path

    def build_zip_in_memory(self) -> io.BytesIO:
        """Create an in-memory ZIP archive suitable for browser downloads."""
        payloads = self.build_export_payloads()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename, data_bytes in payloads.items():
                zf.writestr(filename, data_bytes)
        buffer.seek(0)
        return buffer

    def create_zip_archive(self, target_zip_path: Optional[Path] = None) -> Path:
        """Write a ZIP archive to disk alongside or inside the output directory."""
        dir_path = self.export_to_directory()
        zip_path = target_zip_path or dir_path.with_suffix(".zip")
        buffer = self.build_zip_in_memory()
        zip_path.write_bytes(buffer.getvalue())
        return zip_path
