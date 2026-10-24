"""Service for SkyBlock profile discovery, member normalization, and selection."""

from typing import Any, Dict, List, Optional
from api_client import HypixelAPIClient, ProfileNotFoundError


def get_member_data(members: Dict[str, Any], player_uuid: str) -> Dict[str, Any]:
    """Retrieve player member data safely checking both dashed and undashed UUID keys."""
    if not isinstance(members, dict):
        return {}
    undashed = player_uuid.replace("-", "").strip()
    dashed = HypixelAPIClient.format_dashed_uuid(player_uuid)

    if undashed in members and isinstance(members[undashed], dict):
        return members[undashed]
    if dashed in members and isinstance(members[dashed], dict):
        return members[dashed]
    return {}


def normalize_profiles(raw_profiles: List[Dict[str, Any]], player_uuid: str) -> List[Dict[str, Any]]:
    """Normalize raw profile payloads and sort by last_save timestamp descending."""
    normalized: List[Dict[str, Any]] = []

    for p in raw_profiles:
        if not isinstance(p, dict):
            continue
        members = p.get("members", {})
        member_data = get_member_data(members, player_uuid)
        last_save = member_data.get("last_save", 0)
        if not isinstance(last_save, (int, float)):
            last_save = 0

        normalized.append({
            "profile_id": p.get("profile_id", ""),
            "name": p.get("cute_name", "Unknown"),
            "game_mode": p.get("game_mode", "normal") or "normal",
            "selected": bool(p.get("selected", False)),
            "last_save": int(last_save),
            "data": p,
        })

    normalized.sort(key=lambda x: x["last_save"], reverse=True)
    return normalized


def select_profile(
    profiles: List[Dict[str, Any]],
    requested_name: Optional[str] = None,
    silent: bool = False,
) -> Dict[str, Any]:
    """Select a profile from normalized profiles list."""
    if not profiles:
        raise ProfileNotFoundError("No SkyBlock profiles found for this user.")

    if requested_name:
        req_clean = requested_name.strip().lower()
        for p in profiles:
            if p.get("name", "").lower() == req_clean:
                return p

    if silent or len(profiles) == 1:
        return profiles[0]

    # Interactive CLI selection if terminal is interactive
    print("\nAvailable Profiles:")
    for idx, p in enumerate(profiles, start=1):
        mode_str = f" [{p['game_mode'].upper()}]" if p.get("game_mode") != "normal" else ""
        print(f"  {idx}. {p['name']}{mode_str}")

    while True:
        try:
            choice = input("\nSelect profile [1]: ").strip() or "1"
            if choice.isdigit() and 1 <= int(choice) <= len(profiles):
                return profiles[int(choice) - 1]
        except (EOFError, KeyboardInterrupt):
            return profiles[0]
