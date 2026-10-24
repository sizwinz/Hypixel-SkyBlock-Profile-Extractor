"""Extraction orchestrator for Hypixel SkyBlock profiles and auxiliary endpoints."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from skyblock_extractor.api_client import HypixelAPIClient, SkyBlockExtractorError


@dataclass
class ExtractionResult:
    """Outcome for a single extraction category."""
    category: str
    filename: str
    description: str
    status: str  # "success" | "skipped" | "failed"
    error_message: Optional[str] = None
    data: Optional[Any] = None


ProgressCallback = Callable[[int, int, str, str], None]


class ProfileExtractor:
    """Orchestrates resilient extraction across Hypixel API v2 endpoints."""

    def __init__(
        self,
        client: HypixelAPIClient,
        progress_callback: Optional[ProgressCallback] = None,
    ):
        self.client = client
        self.progress_callback = progress_callback

    def get_endpoint_specs(
        self, player_uuid: str, profile_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Definition of all supported extraction categories and their endpoint mappings."""
        raw_uuid = player_uuid.replace("-", "").strip()
        dashed_uuid = self.client.format_dashed_uuid(player_uuid)

        return {
            "profile": {
                "desc": "Complete Profile Data",
                "filename": "complete_profile.json",
                "endpoint": "skyblock/profile",
                "params": {"profile": profile_id},
                "extract_key": "profile",
            },
            "player": {
                "desc": "Global Player Stats",
                "filename": "player_data.json",
                "endpoint": "player",
                "params": {"uuid": dashed_uuid},
            },
            "garden": {
                "desc": "Garden & Farming Data",
                "filename": "garden_data.json",
                "endpoint": "skyblock/garden",
                "params": {"profile": profile_id},
            },
            "museum": {
                "desc": "Museum Collection Data",
                "filename": "museum_data.json",
                "endpoint": "skyblock/museum",
                "params": {"profile": profile_id},
            },
            "guild": {
                "desc": "Guild Information",
                "filename": "guild_data.json",
                "endpoint": "guild",
                "params": {"player": dashed_uuid},
            },
            "recentgames": {
                "desc": "Recent Minigames",
                "filename": "recent_games.json",
                "endpoint": "recentgames",
                "params": {"uuid": dashed_uuid},
            },
            "status": {
                "desc": "Online Status",
                "filename": "online_status.json",
                "endpoint": "status",
                "params": {"uuid": dashed_uuid},
            },
            "firesales": {
                "desc": "Active Fire Sales",
                "filename": "fire_sales.json",
                "endpoint": "skyblock/firesales",
                "params": {},
            },
            "bingo": {
                "desc": "Bingo Event Stats",
                "filename": "bingo_data.json",
                "endpoint": "skyblock/bingo",
                "params": {"uuid": raw_uuid},
            },
            "bazaar": {
                "desc": "Live Bazaar Prices",
                "filename": "bazaar_prices.json",
                "endpoint": "skyblock/bazaar",
                "params": {},
            },
            "auction": {
                "desc": "Active Profile Auctions",
                "filename": "active_auctions.json",
                "endpoint": "skyblock/auction",
                "params": {"profile": profile_id},
            },
            "news": {
                "desc": "SkyBlock In-game News",
                "filename": "skyblock_news.json",
                "endpoint": "skyblock/news",
                "params": {},
            },
            "items": {
                "desc": "SkyBlock Items Schema",
                "filename": "skyblock_items.json",
                "endpoint": "skyblock/items",
                "params": {},
            },
        }

    def extract(
        self,
        player_uuid: str,
        profile: Dict[str, Any],
        categories: Optional[List[str]] = None,
    ) -> Dict[str, ExtractionResult]:
        """Execute extraction across requested categories resiliently."""
        profile_id = profile.get("profile_id", "").strip()
        all_specs = self.get_endpoint_specs(player_uuid, profile_id)

        target_categories = categories if categories is not None else list(all_specs.keys())
        results: Dict[str, ExtractionResult] = {}
        total = len(target_categories)

        for step, cat in enumerate(target_categories, start=1):
            if cat not in all_specs:
                continue

            spec = all_specs[cat]
            filename = spec["filename"]
            desc = spec["desc"]

            # If profile data is already attached in profile dictionary and matches endpoint
            if cat == "profile":
                try:
                    data = self.client.fetch_endpoint(spec["endpoint"], params=spec["params"])
                    profile_payload = data.get("profile") or profile.get("data") or data
                    results[cat] = ExtractionResult(
                        category=cat,
                        filename=filename,
                        description=desc,
                        status="success",
                        data=profile_payload,
                    )
                    if self.progress_callback:
                        self.progress_callback(step, total, cat, "success")
                    continue
                except Exception as exc:
                    # Fallback to pre-fetched profile data if available
                    if profile.get("data"):
                        results[cat] = ExtractionResult(
                            category=cat,
                            filename=filename,
                            description=desc,
                            status="success",
                            data=profile["data"],
                        )
                        if self.progress_callback:
                            self.progress_callback(step, total, cat, "success")
                        continue
                    sanitized_err = self.client.redact_api_key(str(exc))
                    results[cat] = ExtractionResult(
                        category=cat,
                        filename=filename,
                        description=desc,
                        status="failed",
                        error_message=sanitized_err,
                    )
                    if self.progress_callback:
                        self.progress_callback(step, total, cat, "failed")
                    continue

            try:
                data = self.client.fetch_endpoint(spec["endpoint"], params=spec["params"])
                results[cat] = ExtractionResult(
                    category=cat,
                    filename=filename,
                    description=desc,
                    status="success",
                    data=data,
                )
                if self.progress_callback:
                    self.progress_callback(step, total, cat, "success")
            except Exception as exc:
                sanitized_err = self.client.redact_api_key(str(exc))
                results[cat] = ExtractionResult(
                    category=cat,
                    filename=filename,
                    description=desc,
                    status="failed",
                    error_message=sanitized_err,
                )
                if self.progress_callback:
                    self.progress_callback(step, total, cat, "failed")

        return results
