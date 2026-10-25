"""Hypixel and Mojang API client with security compliance and rate limit handling."""

import os
import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

HYPIXEL_API_URL = "https://api.hypixel.net/v2"
MOJANG_API_URL = "https://api.mojang.com"
DEFAULT_USER_AGENT = "SkyBlock-Profile-Extractor/2.1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_CACHE_TTLS: Dict[str, float] = {
    "resources/skyblock/items": 3600.0,
    "resources/skyblock/skills": 3600.0,
    "resources/skyblock/collections": 3600.0,
    "skyblock/bazaar": 60.0,
    "skyblock/news": 300.0,
    "skyblock/firesales": 300.0,
}


def is_hosted_environment() -> bool:
    """Check if the application is running in a multi-user, server, or cloud hosted context."""
    cloud_indicators = (
        "STREAMLIT_HOSTED",
        "SERVER_NAME",
        "HYPIXEL_API_KEY",
        "RENDER",
        "DYNO",
        "SPACE_ID",
        "FLY_APP_NAME",
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_STATIC_URL",
        "KUBERNETES_SERVICE_HOST",
        "WEBSITE_INSTANCE_ID",
        "STREAMLIT_SHARING_MODE",
    )
    if any(os.environ.get(var) for var in cloud_indicators):
        return True

    if os.environ.get("MULTI_USER", "").lower() in ("1", "true"):
        return True

    if os.environ.get("STREAMLIT_SERVER_HEADLESS", "").lower() in ("1", "true"):
        return True

    return False


def can_persist_key_to_disk() -> bool:
    """Determine whether persisting API keys to local disk is permitted."""
    return not is_hosted_environment()


def is_streamlit_cloud() -> bool:
    """Check if the application is specifically running on Streamlit Community Cloud."""
    if os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("IS_STREAMLIT_CLOUD"):
        return True
    if os.path.exists("/mount/src") and os.path.exists("/home/appuser"):
        return True
    return False


class SkyBlockExtractorError(Exception):
    """Base exception for all SkyBlock Profile Extractor errors."""


class AuthenticationError(SkyBlockExtractorError):
    """Raised when API credentials are missing, invalid, or unauthorized."""


class RateLimitExceededError(SkyBlockExtractorError):
    """Raised when HTTP 429 rate limit is encountered and cannot be fulfilled."""


class PlayerNotFoundError(SkyBlockExtractorError):
    """Raised when a Minecraft username or UUID cannot be resolved."""


class ProfileNotFoundError(SkyBlockExtractorError):
    """Raised when a player has no SkyBlock profiles or target profile is missing."""


class APIResponseError(SkyBlockExtractorError):
    """Raised when the API returns an unexpected, malformed, or error payload."""


class NetworkTimeoutError(SkyBlockExtractorError):
    """Raised when network requests exceed the specified timeout."""


class HypixelAPIClient:
    """Client for official Hypixel API v2 and Mojang API interactions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        max_retry_delay: float = 10.0,
        enable_cache: bool = True,
    ):
        self._api_key = api_key.strip() if api_key else ""
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_retries = max_retries
        self.max_retry_delay = max_retry_delay
        self.enable_cache = enable_cache
        self._cache: Dict[Tuple[str, Tuple[Tuple[str, Any], ...]], Tuple[float, Dict[str, Any]]] = {}
        self.session = requests.Session()

    def clear_cache(self) -> None:
        """Clear all in-memory cached responses."""
        self._cache.clear()

    def __repr__(self) -> str:
        return f"<HypixelAPIClient authenticated={bool(self._api_key)}>"

    @staticmethod
    def format_dashed_uuid(raw_uuid: str) -> str:
        """Format 32-character undashed UUID into standard 8-4-4-4-12 dashed format."""
        clean = raw_uuid.replace("-", "").strip()
        if len(clean) != 32:
            return raw_uuid
        return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"

    def get_player_uuid(self, username: str) -> Tuple[str, str]:
        """Resolve a Minecraft username to (formatted_dashed_uuid, raw_undashed_uuid)."""
        clean_name = username.strip()
        if not re.match(r"^[a-zA-Z0-9_]{1,16}$", clean_name):
            raise PlayerNotFoundError(f"Invalid Minecraft username format: '{clean_name}'")

        url = f"{MOJANG_API_URL}/users/profiles/minecraft/{clean_name}"
        try:
            resp = self.session.get(url, timeout=self.timeout)
            if resp.status_code == 404 or not resp.content:
                raise PlayerNotFoundError(f"Player '{clean_name}' does not exist.")
            resp.raise_for_status()
            data = resp.json()
            raw_uuid = data.get("id")
            if not raw_uuid:
                raise PlayerNotFoundError(f"Mojang response missing player id for '{clean_name}'.")
            return self.format_dashed_uuid(raw_uuid), raw_uuid
        except requests.exceptions.Timeout as exc:
            raise NetworkTimeoutError(f"Connection timed out resolving player '{clean_name}'.") from exc
        except requests.exceptions.RequestException as exc:
            raise SkyBlockExtractorError(f"Network error resolving player: {exc}") from exc

    def fetch_endpoint(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        require_auth: bool = True,
        cache_ttl: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Query a Hypixel API v2 endpoint with in-memory TTL caching and 429 backoff."""
        clean_endpoint = endpoint.lstrip("/")
        url = f"{HYPIXEL_API_URL}/{clean_endpoint}"

        # Determine effective cache TTL
        ttl = cache_ttl
        if ttl is None:
            ttl = DEFAULT_CACHE_TTLS.get(clean_endpoint)

        cache_key = None
        if self.enable_cache and ttl and ttl > 0:
            param_tuple = tuple(sorted((params or {}).items()))
            cache_key = (clean_endpoint, param_tuple)
            cached = self._cache.get(cache_key)
            if cached:
                timestamp, cached_data = cached
                if (time.time() - timestamp) < ttl:
                    return cached_data

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        if require_auth:
            if not self._api_key:
                raise AuthenticationError("Hypixel API Key is required for this endpoint.")
            headers["API-Key"] = self._api_key

        attempt = 0
        while True:
            try:
                resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
                if resp.status_code == 403:
                    raise AuthenticationError("403 Forbidden: Invalid or unauthorized Hypixel API Key.")
                if resp.status_code == 429:
                    reset_header = resp.headers.get("RateLimit-Reset", "")
                    try:
                        reset_sec = float(reset_header) if reset_header else 1.0
                    except (ValueError, TypeError):
                        reset_sec = 1.0

                    base = max(reset_sec, 0.5)
                    backoff = base * (2 ** attempt)

                    if attempt < self.max_retries and backoff <= self.max_retry_delay:
                        attempt += 1
                        sleep_sec = backoff + random.uniform(0.05, 0.2)
                        time.sleep(sleep_sec)
                        continue

                    raise RateLimitExceededError(
                        f"429 Too Many Requests: Rate limit exceeded (reset in {reset_header or 'unknown'}s)."
                    )

                resp.raise_for_status()
                data = resp.json()

                if not isinstance(data, dict):
                    raise APIResponseError("Unexpected response format: expected JSON object.")

                if not data.get("success", False):
                    cause = data.get("cause", "Unknown Hypixel API error")
                    raise APIResponseError(f"Hypixel API Error: {cause}")

                if cache_key is not None and self.enable_cache:
                    self._cache[cache_key] = (time.time(), data)

                return data

            except requests.exceptions.Timeout as exc:
                raise NetworkTimeoutError(f"Hypixel API request timed out ({clean_endpoint}).") from exc
            except (AuthenticationError, RateLimitExceededError, APIResponseError):
                raise
            except requests.exceptions.RequestException as exc:
                msg = self.redact_api_key(str(exc))
                raise SkyBlockExtractorError(f"Hypixel API connection error: {msg}") from exc

    def get_skyblock_profiles(self, player_uuid: str) -> List[Dict[str, Any]]:
        """Fetch all SkyBlock profiles associated with a player UUID."""
        raw_uuid = player_uuid.replace("-", "").strip()
        data = self.fetch_endpoint("skyblock/profiles", params={"uuid": raw_uuid})
        profiles = data.get("profiles")
        if not profiles:
            return []
        return profiles

    def get_skyblock_profile(self, profile_id: str) -> Dict[str, Any]:
        """Fetch detailed data for a specific SkyBlock profile."""
        clean_id = profile_id.strip()
        data = self.fetch_endpoint("skyblock/profile", params={"profile": clean_id})
        profile = data.get("profile")
        if not profile:
            raise ProfileNotFoundError(f"SkyBlock profile '{clean_id}' was not found.")
        return profile

    def redact_api_key(self, message: Optional[str]) -> str:
        """Replace occurrences of the API key with a safe redacted placeholder."""
        if not message:
            return ""
        if self._api_key and len(self._api_key) > 8:
            return message.replace(self._api_key, "[REDACTED_API_KEY]")
        return message
