"""SkyBlock Profile Extractor package."""

from skyblock_extractor.api_client import (
    AuthenticationError,
    HypixelAPIClient,
    PlayerNotFoundError,
    ProfileNotFoundError,
    RateLimitExceededError,
    SkyBlockExtractorError,
)
from skyblock_extractor.profile_service import normalize_profiles, select_profile
from skyblock_extractor.extractor import ProfileExtractor, ExtractionResult
from skyblock_extractor.analysis import ProfileAnalyzer
from skyblock_extractor.exporter import ProfileExporter

__version__ = "2.1.0"

__all__ = [
    "AuthenticationError",
    "HypixelAPIClient",
    "PlayerNotFoundError",
    "ProfileNotFoundError",
    "RateLimitExceededError",
    "SkyBlockExtractorError",
    "normalize_profiles",
    "select_profile",
    "ProfileExtractor",
    "ExtractionResult",
    "ProfileAnalyzer",
    "ProfileExporter",
    "__version__",
]
