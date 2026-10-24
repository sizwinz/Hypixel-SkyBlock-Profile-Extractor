"""Hypixel and Mojang API client with security compliance and rate limit handling."""

from typing import Any, Dict, List, Optional, Tuple


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

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key.strip() if api_key else ""

    def redact_api_key(self, message: Optional[str]) -> str:
        """Replace occurrences of the API key with a safe redacted placeholder."""
        if not message:
            return ""
        if self._api_key and len(self._api_key) > 8:
            return message.replace(self._api_key, "[REDACTED_API_KEY]")
        return message
