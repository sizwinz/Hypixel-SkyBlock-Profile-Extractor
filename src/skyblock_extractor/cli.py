"""Command-line interface implementation for SkyBlock extraction."""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from skyblock_extractor.api_client import (
    AuthenticationError,
    HypixelAPIClient,
    PlayerNotFoundError,
    ProfileNotFoundError,
    RateLimitExceededError,
    SkyBlockExtractorError,
)
from skyblock_extractor.profile_service import normalize_profiles, select_profile as select_profile_service
from skyblock_extractor.extractor import ProfileExtractor
from skyblock_extractor.analysis import ProfileAnalyzer
from skyblock_extractor.exporter import ProfileExporter

VERSION = "2.1.0"


class Colors:
    """ANSI color sequences for executive terminal styling."""
    HEADER = "\033[96m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    INFO = "\033[94m"
    ACCENT = "\033[95m"
    END = "\033[0m"


def print_header(title: str) -> None:
    print(f"\n{Colors.HEADER}>> {title}{Colors.END}")
    print(f"{Colors.HEADER}{'-' * 50}{Colors.END}")


def print_success(msg: str) -> None:
    print(f"{Colors.SUCCESS}[OK] {msg}{Colors.END}")


def print_info(msg: str) -> None:
    print(f"{Colors.INFO}[i]  {msg}{Colors.END}")


def print_warning(msg: str) -> None:
    print(f"{Colors.WARNING}[!]  {msg}{Colors.END}")


def print_error(msg: str) -> None:
    print(f"{Colors.ERROR}[X]  {msg}{Colors.END}")


def get_api_key(silent: bool = False, explicit_key: Optional[str] = None) -> str:
    """Resolve API key from explicit param, environment variable, api_key.txt, or interactive prompt."""
    if explicit_key and len(explicit_key.strip()) > 30:
        return explicit_key.strip()

    env_key = os.environ.get("HYPIXEL_API_KEY", "").strip()
    if len(env_key) > 30:
        if not silent:
            print_info("Loaded API key from HYPIXEL_API_KEY environment variable")
        return env_key

    key_file = Path("api_key.txt")
    if key_file.exists():
        try:
            file_key = key_file.read_text(encoding="utf-8").strip()
            if len(file_key) > 30:
                if not silent:
                    print_info("Loaded API key from api_key.txt")
                return file_key
        except Exception:
            pass

    if silent:
        raise AuthenticationError("Hypixel API Key not found (Required for silent mode).")

    print_warning("Hypixel API Key not found!")
    print("  1. Navigate to https://developer.hypixel.net")
    print("  2. Sign in and generate your Development or Personal API Key")

    while True:
        try:
            key_input = input(f"\n{Colors.ACCENT}Enter Hypixel API Key: {Colors.END}").strip()
            if len(key_input) > 30:
                try:
                    key_file.write_text(key_input, encoding="utf-8")
                    print_success("API Key saved to api_key.txt")
                except Exception as e:
                    print_warning(f"Could not persist API key to disk: {e}")
                return key_input
            print_error("Invalid API key format (must be standard UUID format). Please try again.")
        except (KeyboardInterrupt, EOFError):
            raise AuthenticationError("API key input cancelled by user.")


def get_player_uuid(username: str, client: Optional[HypixelAPIClient] = None) -> Tuple[str, str]:
    """Resolve Minecraft player username to (dashed_uuid, raw_uuid)."""
    api = client or HypixelAPIClient()
    return api.get_player_uuid(username)


def get_profiles(uuid: str, api_key: str) -> List[Dict[str, Any]]:
    """Fetch and normalize all SkyBlock profiles for the player UUID."""
    client = HypixelAPIClient(api_key=api_key)
    raw_profiles = client.get_skyblock_profiles(uuid)
    if not raw_profiles:
        raise ProfileNotFoundError("No SkyBlock profiles found for this player.")
    return normalize_profiles(raw_profiles, uuid)


def select_profile(
    profiles: List[Dict[str, Any]],
    requested_name: Optional[str] = None,
    silent: bool = False,
) -> Dict[str, Any]:
    """Select target profile matching name, or auto-select most recently played."""
    return select_profile_service(profiles, requested_name=requested_name, silent=silent)


def extract_data(
    uuid: str,
    profile: Dict[str, Any],
    api_key: str,
    username: str,
    custom_out_dir: Optional[Path] = None,
    create_zip: bool = False,
) -> Tuple[Path, int]:
    """Orchestrate extraction, analysis, and file export for a selected profile."""
    client = HypixelAPIClient(api_key=api_key)
    extractor = ProfileExtractor(client=client)

    print_header("Starting Data Extraction")
    print_info(f"Player: {username} ({uuid})")
    print_info(f"Profile: {profile['name']} [{profile.get('game_mode', 'normal')}]")

    results = extractor.extract(player_uuid=uuid, profile=profile)

    # Prioritize freshly extracted profile data if available
    fresh_profile_data = None
    if "profile" in results and results["profile"].status == "success" and results["profile"].data:
        fresh_profile_data = results["profile"].data

    profile_payload_for_analysis = fresh_profile_data or profile.get("data", profile)

    # Perform progression analysis
    analyzer = ProfileAnalyzer()
    auxiliary = {cat: res.data for cat, res in results.items() if res.status == "success" and res.data}
    summary = analyzer.analyze(
        player_uuid=uuid,
        profile_data=profile_payload_for_analysis,
        auxiliary_data=auxiliary,
    )

    # Export to disk
    exporter = ProfileExporter(
        username=username,
        player_uuid=uuid,
        profile_name=profile["name"],
        profile_id=profile["profile_id"],
        results=results,
        summary=summary,
        custom_out_dir=custom_out_dir,
    )

    out_dir = exporter.export_to_directory()

    if create_zip:
        zip_path = exporter.create_zip_archive()
        print_success(f"Created ZIP archive: {zip_path.name}")

    successful_count = sum(1 for r in results.values() if r.status == "success")
    return out_dir, successful_count


def main() -> None:
    """CLI entry point for standalone extraction."""
    parser = argparse.ArgumentParser(description="Hypixel SkyBlock Profile Extractor v2.1")
    parser.add_argument("username", nargs="?", help="Minecraft Username")
    parser.add_argument("-p", "--profile", help="Target SkyBlock profile name (e.g. Tomato)")
    parser.add_argument("-s", "--silent", action="store_true", help="Non-interactive execution")
    parser.add_argument("--api-key", help="Explicit Hypixel API key")
    parser.add_argument("--output-dir", help="Custom directory for exported files")
    parser.add_argument("--zip", action="store_true", help="Generate a ZIP archive of extracted files")
    args = parser.parse_args()

    print_header(f"SkyBlock Extractor v{VERSION}")

    try:
        api_key = get_api_key(silent=args.silent, explicit_key=args.api_key)

        username = args.username
        if not username:
            if args.silent:
                print_error("Minecraft username is required in silent mode.")
                sys.exit(1)
            username = input("Enter Minecraft Username: ").strip()

        dashed_uuid, raw_uuid = get_player_uuid(username)
        print_success(f"Found player: {username} ({dashed_uuid})")

        profiles = get_profiles(dashed_uuid, api_key)
        print_success(f"Found {len(profiles)} SkyBlock profile(s)")

        selected = select_profile(profiles, requested_name=args.profile, silent=args.silent)
        print_success(f"Selected profile: {selected['name']} [{selected['game_mode']}]")

        custom_path = Path(args.output_dir) if args.output_dir else None
        out_dir, count = extract_data(
            uuid=dashed_uuid,
            profile=selected,
            api_key=api_key,
            username=username,
            custom_out_dir=custom_path,
            create_zip=args.zip,
        )

        print_header("Extraction Complete")
        print_success(f"Extracted {count} data files to: {out_dir}")
        print_info("Generated files include 'complete_profile.json', 'profile_summary.json', and 'extraction_manifest.json'.")
        sys.exit(0)

    except SkyBlockExtractorError as exc:
        print_error(f"Extraction failed: {exc}")
        sys.exit(1)
    except KeyboardInterrupt:
        print_warning("\nExecution cancelled by user.")
        sys.exit(130)
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
