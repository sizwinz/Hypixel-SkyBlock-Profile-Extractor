"""Hypixel and Mojang API client with security compliance and rate limit handling."""

import requests
from typing import Any, Dict, List, Optional, Tuple
import re

HYPIXEL_API_URL = "https://api.hypixel.net/v2"
MOJANG_API_URL = "https://api.mojang.com"
DEFAULT_USER_AGENT = "SkyBlock-Profile-Extractor/2.1"
DEFAULT_TIMEOUT = 30.0


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
    ):
        self._api_key = api_key.strip() if api_key else ""
        self.timeout = timeout
        self.user_agent = user_agent
        self.session = requests.Session()

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
    ) -> Dict[str, Any]:
        """Query a Hypixel API v2 endpoint using HTTP header authentication."""
        clean_endpoint = endpoint.lstrip("/")
        url = f"{HYPIXEL_API_URL}/{clean_endpoint}"

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        if require_auth:
            if not self._api_key:
                raise AuthenticationError("Hypixel API Key is required for this endpoint.")
            headers["API-Key"] = self._api_key

        try:
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            if resp.status_code == 403:
                raise AuthenticationError("403 Forbidden: Invalid or unauthorized Hypixel API Key.")
            if resp.status_code == 429:
                reset_sec = resp.headers.get("RateLimit-Reset", "unknown")
                raise RateLimitExceededError(
                    f"429 Too Many Requests: Rate limit exceeded (reset in {reset_sec}s)."
                )

            resp.raise_for_status()
            data = resp.json()

            if not isinstance(data, dict):
                raise APIResponseError("Unexpected response format: expected JSON object.")

            if not data.get("success", False):
                cause = data.get("cause", "Unknown Hypixel API error")
                raise APIResponseError(f"Hypixel API Error: {cause}")

            return data

        except requests.exceptions.Timeout as exc:
            raise NetworkTimeoutError(f"Hypixel API request timed out ({clean_endpoint}).") from exc
        except (AuthenticationError, RateLimitExceededError, APIResponseError):
            raise
        except requests.exceptions.RequestException as exc:
            msg = self.redact_api_key(str(exc))
            raise SkyBlockExtractorError(f"Hypixel API connection error: {msg}") from exc

    def redact_api_key(self, message: Optional[str]) -> str:
        """Replace occurrences of the API key with a safe redacted placeholder."""
        if not message:
            return ""
        if self._api_key and len(self._api_key) > 8:
            return message.replace(self._api_key, "[REDACTED_API_KEY]")
        return message
