"""Human-readable profile analysis, skill progression, and explainable recommendations."""

from typing import Any, Dict, List, Optional
from skyblock_extractor.profile_service import get_member_data

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
        experience_dict = player_data.get("experience", {}) if isinstance(player_data, dict) else {}

        has_any_skills = False
        for skill in self.SKILLS_TO_TRACK:
            skill_upper = f"SKILL_{skill.upper()}"
            old_skill_key = f"experience_skill_{skill}"

            if old_skill_key in member:
                raw_xp = member[old_skill_key]
            elif isinstance(experience_dict, dict) and skill_upper in experience_dict:
                raw_xp = experience_dict[skill_upper]
            else:
                raw_xp = None

            if raw_xp is not None:
                has_any_skills = True
                level = calculate_level(float(raw_xp), SKILL_XP_THRESHOLDS)
                skills_summary[skill] = {
                    "xp": float(raw_xp),
                    "level": level,
                    "available": True,
                }
                if skill in ["combat", "mining", "farming", "foraging", "fishing", "enchanting", "alchemy", "taming"]:
                    total_level += level
                    tracked_count += 1
            else:
                skills_summary[skill] = {
                    "xp": None,
                    "level": None,
                    "available": False,
                }

        skill_average = round(total_level / tracked_count, 2) if tracked_count > 0 else None

        # 3. Slayers
        slayer_obj = member.get("slayer")
        slayer_summary: Dict[str, Any] = {"available": False, "bosses": {}}
        if isinstance(slayer_obj, dict) and "slayer_bosses" in slayer_obj:
            slayer_data = slayer_obj.get("slayer_bosses", {})
            if isinstance(slayer_data, dict) and slayer_data:
                slayer_summary["available"] = True
                for boss, val in slayer_data.items():
                    if isinstance(val, dict):
                        xp = val.get("xp", 0)
                        entry = {
                            "xp": xp,
                            "level": calculate_level(float(xp), SLAYER_XP_THRESHOLDS),
                        }
                        slayer_summary["bosses"][boss] = entry
                        slayer_summary[boss] = entry

        # 4. Dungeons / Catacombs
        dungeons_obj = member.get("dungeons")
        dungeons_available = isinstance(dungeons_obj, dict) and bool(dungeons_obj.get("dungeon_types"))
        if dungeons_available and isinstance(dungeons_obj, dict):
            cata_xp = dungeons_obj.get("dungeon_types", {}).get("catacombs", {}).get("experience", 0)
            selected_class = dungeons_obj.get("selected_dungeon_class", "none")
            cata_level = calculate_level(float(cata_xp), CATACOMBS_XP_THRESHOLDS)
            dungeons_summary = {
                "available": True,
                "catacombs_xp": float(cata_xp),
                "catacombs_level": cata_level,
                "class": selected_class,
            }
        else:
            dungeons_summary = {
                "available": False,
                "catacombs_xp": None,
                "catacombs_level": None,
                "class": "none",
            }

        # 5. Mining & Heart of the Mountain
        mining_core = member.get("mining_core")
        mining_available = isinstance(mining_core, dict) and bool(mining_core)
        if mining_available and isinstance(mining_core, dict):
            mining_summary = {
                "available": True,
                "tokens": mining_core.get("tokens", 0),
                "mithril_powder": mining_core.get("powder_mithril", 0),
                "gemstone_powder": mining_core.get("powder_gemstone", 0),
            }
        else:
            mining_summary = {
                "available": False,
                "tokens": None,
                "mithril_powder": None,
                "gemstone_powder": None,
            }

        # 6. Garden & Farming
        garden_container = aux.get("garden")
        garden_available = isinstance(garden_container, dict) and "garden" in garden_container
        if garden_available and isinstance(garden_container, dict):
            garden_raw = garden_container.get("garden", {})
            garden_summary = {
                "available": True,
                "level": garden_raw.get("level", 0),
                "completed_visitors": garden_raw.get("completed_visitors", 0),
            }
        else:
            garden_summary = {
                "available": False,
                "level": None,
                "completed_visitors": None,
            }

        # 7. Privacy & Missing APIs
        skills_disabled = bool(member) and not has_any_skills
        api_privacy: Dict[str, bool] = {
            "skills_api_disabled": skills_disabled,
            "inventory_api_disabled": bool(member) and ("inv_contents" not in member and "inventory" not in member),
            "banking_api_disabled": "banking" not in profile_data,
        }

        # 8. Progression Priorities (Rule-Based & Explainable)
        priorities: List[str] = []
        if skill_average is not None and skill_average < 25:
            priorities.append("Skill Average Foundation: Raise non-combat skills (Farming, Mining, Enchanting) to reach Skill Average 25.")
        elif skill_average is None and skills_disabled:
            priorities.append("API Privacy: Enable Skills and Inventory API in Hypixel SkyBlock settings to view skill progression.")
        if dungeons_summary["available"] and dungeons_summary["catacombs_level"] is not None and dungeons_summary["catacombs_level"] < 14:
            priorities.append("Catacombs Entry: Progress through Catacombs Floors 1-5 to unlock essential mid-game dungeon gear.")

        wolf_boss = slayer_summary.get("wolf") or slayer_summary.get("bosses", {}).get("wolf")
        if slayer_summary["available"] and wolf_boss and wolf_boss.get("level", 0) < 6:
            priorities.append("Slayer Utility: Advance Wolf Slayer to Level 6 to unlock the Mana Flux Power Orb.")

        if garden_summary["available"] and garden_summary["level"] is not None and garden_summary["level"] < 5:
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
