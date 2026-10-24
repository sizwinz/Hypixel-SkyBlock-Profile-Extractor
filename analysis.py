"""Human-readable profile analysis, skill progression, and explainable recommendations."""

from typing import Any, Dict, List, Optional
from profile_service import get_member_data

# Cumulative XP thresholds for skills 1 through 50
SKILL_XP_THRESHOLDS = [
    50, 175, 375, 675, 1175, 1925, 2925, 4425, 6425, 9925,
    14925, 22425, 32425, 47425, 67425, 97425, 147425, 222425, 322425, 522425,
    822425, 1222425, 1722425, 2322425, 3022425, 3822425, 4722425, 5722425, 6822425, 8022425,
    9322425, 10722425, 12222425, 13822425, 15522425, 17322425, 19222425, 21222425, 23322425, 25522425,
    27822425, 30222425, 32722425, 35322425, 38072425, 40972425, 44072425, 47472425, 51172425, 55172425,
]

# Cumulative Catacombs XP thresholds 1 through 50
CATACOMBS_XP_THRESHOLDS = [
    50, 125, 235, 395, 625, 955, 1425, 2095, 3045, 4385,
    6275, 8940, 12700, 17960, 25340, 35640, 50040, 70040, 97640, 135640,
    188140, 259640, 356640, 488640, 668640, 911640, 1239640, 1681640, 2276640, 3076640,
    4146640, 5576640, 7486640, 10036640, 13436640, 17936640, 23836640, 31536640, 41436640, 54136640,
    70336640, 90836640, 116636640, 148936640, 189236640, 239436640, 301936640, 379436640, 474436640, 569436640,
]

SLAYER_XP_THRESHOLDS = [5, 15, 200, 1000, 5000, 20000, 100000, 400000, 1000000]


def calculate_level(xp: float, thresholds: List[int]) -> int:
    """Calculate integer level from cumulative XP."""
    level = 0
    for threshold in thresholds:
        if xp >= threshold:
            level += 1
        else:
            break
    return level


class ProfileAnalyzer:
    """Computes transparent, explainable player progression metrics."""

    SKILLS_TO_TRACK = [
        "combat", "mining", "farming", "foraging", "fishing",
        "enchanting", "alchemy", "taming", "carpentry"
    ]

    def analyze(
        self,
        player_uuid: str,
        profile_data: Dict[str, Any],
        auxiliary_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Perform deterministic analysis over extracted profile and auxiliary data."""
        members = profile_data.get("members", {})
        member = get_member_data(members, player_uuid)
        aux = auxiliary_data or {}

        # 1. Profile metadata
        profile_name = profile_data.get("cute_name", "Unknown")
        game_mode = profile_data.get("game_mode", "normal") or "normal"

        # 2. Skills
        skills_summary: Dict[str, Dict[str, Any]] = {}
        total_level = 0
        tracked_count = 0

        player_data = member.get("player_data", {})
        experience_dict = player_data.get("experience", {})

        for skill in self.SKILLS_TO_TRACK:
            xp = (
                member.get(f"experience_skill_{skill}")
                or experience_dict.get(f"SKILL_{skill.upper()}", 0)
                or 0
            )
            level = calculate_level(float(xp), SKILL_XP_THRESHOLDS)
            skills_summary[skill] = {
                "xp": float(xp),
                "level": level,
            }
            if skill in ["combat", "mining", "farming", "foraging", "fishing", "enchanting", "alchemy", "taming"]:
                total_level += level
                tracked_count += 1

        skill_average = round(total_level / max(tracked_count, 1), 2)

        # 3. Slayers
        slayer_data = member.get("slayer", {}).get("slayer_bosses", {})
        slayer_summary: Dict[str, Dict[str, Any]] = {}
        for boss, val in slayer_data.items():
            if isinstance(val, dict):
                xp = val.get("xp", 0)
                slayer_summary[boss] = {
                    "xp": xp,
                    "level": calculate_level(float(xp), SLAYER_XP_THRESHOLDS),
                }

        # 4. Dungeons / Catacombs
        dungeons_obj = member.get("dungeons", {})
        cata_xp = dungeons_obj.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)
        selected_class = dungeons_obj.get("selected_dungeon_class", "none")
        cata_level = calculate_level(float(cata_xp), CATACOMBS_XP_THRESHOLDS)

        dungeons_summary = {
            "catacombs_xp": float(cata_xp),
            "catacombs_level": cata_level,
            "class": selected_class,
        }

        # 5. Mining & Heart of the Mountain
        mining_core = member.get("mining_core", {})
        hotm_tokens = mining_core.get("tokens", 0)
        mithril_powder = mining_core.get("powder_mithril", 0)
        gemstone_powder = mining_core.get("powder_gemstone", 0)
        mining_summary = {
            "tokens": hotm_tokens,
            "mithril_powder": mithril_powder,
            "gemstone_powder": gemstone_powder,
        }

        # 6. Garden & Farming
        garden_raw = aux.get("garden", {}).get("garden", {})
        garden_summary = {
            "level": garden_raw.get("level", 0),
            "completed_visitors": garden_raw.get("completed_visitors", 0),
        }

        # 7. Privacy & Missing APIs
        api_privacy: Dict[str, bool] = {
            "skills_api_disabled": total_level == 0 and bool(member),
            "inventory_api_disabled": "inv_contents" not in member and "inventory" not in member,
            "banking_api_disabled": "banking" not in profile_data,
        }

        # 8. Progression Priorities (Rule-Based & Explainable)
        priorities: List[str] = []
        if skill_average < 25:
            priorities.append("Skill Average Foundation: Raise non-combat skills (Farming, Mining, Enchanting) to reach Skill Average 25.")
        if cata_level < 14:
            priorities.append("Catacombs Entry: Progress through Catacombs Floors 1-5 to unlock essential mid-game dungeon gear.")
        if slayer_summary.get("wolf", {}).get("level", 0) < 6:
            priorities.append("Slayer Utility: Advance Wolf Slayer to Level 6 to unlock the Mana Flux Power Orb.")
        if garden_summary["level"] < 5:
            priorities.append("Garden Initialization: Unlock initial Garden plots and serve visitors to boost farming fortune.")
        if not priorities:
            priorities.append("Endgame Progression: Focus on Master Catacombs floors, Heart of the Mountain 7/10 tree completion, and high-tier Slayer bosses.")

        # 9. Disclaimers
        disclaimers = {
            "net_worth": (
                "Bazaar prices and raw inventory exports reflect market snapshots and do not "
                "constitute an authoritative player net worth calculation without complete NBT "
                "decoding and auction evaluation."
            ),
            "api_privacy": (
                "Progression statistics rely directly on enabled Hypixel in-game API privacy "
                "settings (API Settings in the SkyBlock menu)."
            ),
            "historical_tracking": (
                "This report represents an explicit, on-demand point-in-time snapshot. "
                "No automated or continuous tracking is performed."
            ),
        }

        return {
            "profile_name": profile_name,
            "game_mode": game_mode,
            "skill_average": skill_average,
            "skills": skills_summary,
            "slayer": slayer_summary,
            "dungeons": dungeons_summary,
            "mining": mining_summary,
            "garden": garden_summary,
            "api_privacy": api_privacy,
            "progression_priorities": priorities,
            "disclaimers": disclaimers,
        }
