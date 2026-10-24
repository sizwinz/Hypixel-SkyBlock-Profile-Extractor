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
