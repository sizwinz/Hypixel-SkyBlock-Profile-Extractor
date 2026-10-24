"""Backwards-compatible CLI entry point and wrapper for skyblock_extractor."""

from skyblock_extractor.cli import (
    main,
    get_api_key,
    get_player_uuid,
    get_profiles,
    select_profile,
    extract_data,
    Colors,
    print_header,
    print_success,
    print_info,
    print_warning,
    print_error,
    VERSION,
)

if __name__ == "__main__":
    main()
