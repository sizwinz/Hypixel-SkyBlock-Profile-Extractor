#!/usr/bin/env python3
"""
SkyBlock Profile Extractor - Python Edition
Extract complete Hypixel SkyBlock profile data for AI analysis

Author: SkyBlock Profile Extractor Team
Repository: https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor
Version: 1
"""

import requests
import json
import os
import time
import sys
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import argparse

# Configuration
VERSION = "1"
BASE_URL = "https://cupcake.shiiyu.moe/api"
USER_AGENT = f"SkyBlock-Profile-Extractor/{VERSION}"
RATE_LIMIT = 0.5  # seconds between requests
TIMEOUT = 30  # seconds

# Color codes for terminal output
class Colors:
    HEADER = '\033[96m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    ACCENT = '\033[95m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str, silent: bool = False) -> None:
    """Print a formatted header."""
    if not silent:
        print(f"\n{Colors.HEADER}>> {title}{Colors.END}")
        print(f"{Colors.HEADER}{'-' * 50}{Colors.END}")

def print_success(message: str, silent: bool = False) -> None:
    """Print a success message."""
    if not silent:
        print(f"{Colors.SUCCESS}[+] {message}{Colors.END}")

def print_info(message: str, silent: bool = False) -> None:
    """Print an info message."""
    if not silent:
        print(f"{Colors.INFO}[i] {message}{Colors.END}")

def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}[!] {message}{Colors.END}")

def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.ERROR}[X] {message}{Colors.END}")

def make_api_call(endpoint: str, context: str = "API call", ignore_403: bool = False) -> Optional[Dict]:
    """Make an API call with proper error handling and rate limiting."""
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(endpoint, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        
        time.sleep(RATE_LIMIT)
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if ignore_403 and e.response.status_code == 403:
            raise Exception("403 Forbidden")
        if e.response.status_code == 403:
            raise Exception(f"{context} failed - API access denied (check SkyBlock API settings)")
        elif e.response.status_code == 404:
            raise Exception(f"{context} failed - data not found")
        else:
            raise Exception(f"{context} failed - HTTP {e.response.status_code}")
    except Exception as e:
        raise Exception(f"{context} failed - {str(e)}")


def get_player_uuid(username: str, silent: bool = False) -> Optional[Dict]:
    """Get player UUID from username."""
    print_info(f"Looking up UUID for {username}...", silent)
    
    try:
        response = make_api_call(f"{BASE_URL}/uuid/{username}", "UUID lookup")
        
        if response and 'uuid' in response:
            print_success(f"Found player: {response['username']} ({response['uuid'][:8]}...)", silent)
            return response
        else:
            raise Exception("Player not found")
    
    except Exception as e:
        print_error(f"Failed to find player '{username}': {str(e)}")
        print_warning("Make sure the username is spelled correctly and the player exists.")
        return None

def get_player_profiles(uuid: str, username: str, silent: bool = False) -> Optional[List[Dict]]:
    """Get player's SkyBlock profiles with fallback."""
    print_info("Fetching SkyBlock profiles...", silent)
    
    # Try comprehensive endpoint first
    try:
        response = make_api_call(f"{BASE_URL}/profiles/{uuid}", "Full profile lookup", ignore_403=True)
        if response and 'profiles' in response and response['profiles']:
            profile_list = []
            for profile_id, profile_data in response['profiles'].items():
                profile_list.append({
                    'profile_id': profile_data.get('profile_id'),
                    'profile_cute_name': profile_data.get('cute_name'),
                    'selected': profile_data.get('selected', False)
                })
            print_success(f"Found {len(profile_list)} profiles.", silent)
            return profile_list
    except Exception as e:
        if "403 Forbidden" in str(e):
            print_warning("Could not fetch all profiles (API permissions likely restricted). Falling back to active profile only.")
        else:
            print_warning(f"Could not fetch all profiles: {str(e)}. Falling back to active profile only.")

    # Fallback to stats endpoint for active profile
    try:
        response = make_api_call(f"{BASE_URL}/stats/{uuid}", "Active profile lookup")
        if response and 'stats' in response:
            profile = {
                'profile_id': response['stats']['profile_id'],
                'profile_cute_name': response['stats']['profile_cute_name'],
                'selected': True
            }
            print_success(f"Found active profile: (T) {profile['profile_cute_name']}", silent)
            return [profile]
        else:
            raise Exception("No active SkyBlock profile found")
    except Exception as e:
        print_error(f"Failed to fetch any profiles for '{username}': {str(e)}")
        return None


def select_profile(profiles: List[Dict], requested_profile: str = None, silent: bool = False) -> Optional[Dict]:
    """Select a profile from the available profiles."""
    if not profiles:
        return None
    if len(profiles) == 1:
        return profiles[0]
    
    if requested_profile:
        for profile in profiles:
            if profile['profile_cute_name'].lower() == requested_profile.lower():
                return profile
        
        print_warning(f"Profile '{requested_profile}' not found. Available profiles:")
        for i, profile in enumerate(profiles, 1):
            print(f"  {i}. {profile['profile_cute_name']}")
    
    if not silent:
        print(f"\n{Colors.INFO}[i] Available profiles:{Colors.END}")
        for i, profile in enumerate(profiles, 1):
            emoji = "(T)" if profile.get('selected') else "(C)"
            selected = " (Selected)" if profile.get('selected') else ""
            print(f"  {i}. {emoji} {profile['profile_cute_name']}{selected}")
        
        while True:
            try:
                choice = input("Select profile [1]: ").strip() or "1"
                index = int(choice) - 1
                if 0 <= index < len(profiles):
                    return profiles[index]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
            except KeyboardInterrupt:
                print("\nOperation cancelled.")
                return None
    else:
        # In silent mode, use the selected profile or the first one
        for profile in profiles:
            if profile.get('selected'):
                return profile
        return profiles[0]

def create_output_directory(username: str, profile_name: str) -> Optional[str]:
    """Create a timestamped output directory with username and profile name."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize profile name
    safe_profile_name = "".join(c for c in profile_name if c.isalnum() or c in (' ', '_')).rstrip()
    output_dir = f"{username}_{safe_profile_name}_{timestamp}"
    
    try:
        Path(output_dir).mkdir(exist_ok=True)
        print_success(f"Created output directory: {output_dir}")
        return output_dir
    except Exception as e:
        print_error(f"Failed to create output directory: {str(e)}")
        return None

def save_profile_data(endpoint: str, output_file: str, output_dir: str, description: str, silent: bool = False) -> bool:
    """Save profile data from an API endpoint to a file."""
    try:
        print_info(f"Extracting {description}...", silent)
        response = make_api_call(endpoint, description)
        
        file_path = Path(output_dir) / output_file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2, ensure_ascii=False)
        
        print_success(f"Saved {description}", silent)
        return True
    
    except Exception as e:
        print_warning(f"Failed to extract {description}: {str(e)}")
        return False

def extract_profile_data(uuid: str, profile_id: str, output_dir: str, silent: bool = False) -> Dict[str, int]:
    """Extract all profile data."""
    print_header("Extracting Profile Data", silent)
    
    # Define extraction plan
    extraction_plan = [
        {"endpoint": f"stats/{uuid}/{profile_id}", "file": "stats.json", "description": "Profile Statistics"},
        {"endpoint": f"playerStats/{uuid}/{profile_id}", "file": "player_stats.json", "description": "Player Performance"},
        {"endpoint": f"networth/{uuid}/{profile_id}", "file": "networth.json", "description": "Networth Analysis"},
        {"endpoint": f"skills/{uuid}/{profile_id}", "file": "skills.json", "description": "Skills & XP"},
        {"endpoint": f"dungeons/{uuid}/{profile_id}", "file": "dungeons.json", "description": "Dungeon Progress"},
        {"endpoint": f"slayer/{uuid}/{profile_id}", "file": "slayer.json", "description": "Slayer Statistics"},
        {"endpoint": f"collections/{uuid}/{profile_id}", "file": "collections.json", "description": "Collection Progress"},
        {"endpoint": f"gear/{uuid}/{profile_id}", "file": "gear.json", "description": "Equipment & Gear"},
        {"endpoint": f"accessories/{uuid}/{profile_id}", "file": "accessories.json", "description": "Accessories & Talismans"},
        {"endpoint": f"pets/{uuid}/{profile_id}", "file": "pets.json", "description": "Pet Collection"},
        {"endpoint": f"minions/{uuid}/{profile_id}", "file": "minions.json", "description": "Minion Data"},
        {"endpoint": f"bestiary/{uuid}/{profile_id}", "file": "bestiary.json", "description": "Bestiary Progress"},
        {"endpoint": f"crimson_isle/{uuid}/{profile_id}", "file": "crimson_isle.json", "description": "Crimson Isle Progress"},
        {"endpoint": f"rift/{uuid}/{profile_id}", "file": "rift.json", "description": "Rift Dimension"},
        {"endpoint": f"misc/{uuid}/{profile_id}", "file": "misc.json", "description": "Miscellaneous Data"},
        {"endpoint": f"garden/{profile_id}", "file": "garden.json", "description": "Garden Progress"},
    ]
    
    # Inventory endpoints
    inventory_types = [
        {"type": "inv_contents", "description": "Main Inventory"},
        {"type": "ender_chest_contents", "description": "Ender Chest"},
        {"type": "wardrobe_contents", "description": "Wardrobe"},
        {"type": "personal_vault_contents", "description": "Personal Vault"},
        {"type": "bag_contents", "description": "All Bags"},
        {"type": "fishing_bag", "description": "Fishing Bag"},
        {"type": "potion_bag", "description": "Potion Bag"},
        {"type": "candy_inventory_contents", "description": "Candy Inventory"},
        {"type": "quiver", "description": "Quiver"},
    ]
    
    for inv in inventory_types:
        extraction_plan.append({
            "endpoint": f"inventory/{uuid}/{profile_id}/{inv['type']}",
            "file": f"inventory_{inv['type']}.json",
            "description": inv['description']
        })
    
    success_count = 0
    total_count = len(extraction_plan)
    
    for item in extraction_plan:
        endpoint = f"{BASE_URL}/{item['endpoint']}"
        success = save_profile_data(endpoint, item['file'], output_dir, item['description'], silent)
        if success:
            success_count += 1
    
    return {
        'success': success_count,
        'total': total_count,
        'success_rate': round((success_count / total_count) * 100, 1)
    }

def show_summary(results: Dict[str, int], output_dir: str, username: str, silent: bool = False) -> None:
    """Show extraction summary."""
    print_header("Extraction Summary", silent)
    
    print(f"{Colors.SUCCESS}[*] Data extraction completed!{Colors.END}")
    print(f"{Colors.INFO}[i] Output directory: {output_dir}{Colors.END}")
    print(f"{Colors.INFO}[i] Files extracted: {results['success']}/{results['total']}{Colors.END}")
    print(f"{Colors.SUCCESS}[>] Success rate: {results['success_rate']}%{Colors.END}")
    
    # Calculate directory size
    total_size = sum(f.stat().st_size for f in Path(output_dir).rglob('*') if f.is_file())
    size_kb = round(total_size / 1024, 1)
    size_mb = round(total_size / (1024 * 1024), 1)
    
    size_display = f"{size_mb} MB" if size_mb > 1 else f"{size_kb} KB"
    print(f"{Colors.INFO}[S] Total size: {size_display}{Colors.END}")
    
    print(f"\n{Colors.ACCENT}[A] Ready for AI analysis!{Colors.END}")
    print(f"{Colors.INFO}Your complete SkyBlock profile data is now available for:{Colors.END}")
    print("  - AI-powered progression analysis")
    print("  - Personal performance tracking")
    print("  - Data visualization projects")
    print("  - Optimization recommendations")
    
    print(f"\n{Colors.HEADER}[N] Next Steps:{Colors.END}")
    print(f"  1. Zip the '{output_dir}' folder for easy sharing")
    print("  2. Upload to your preferred AI assistant (ChatGPT, Claude, etc.)")
    print("  3. Ask for progression analysis and recommendations!")
    
    if not silent:
        input(f"\n{Colors.INFO}Press Enter to continue...{Colors.END}")

def test_prerequisites() -> bool:
    """Test if all prerequisites are met."""
    # Check Python version
    if sys.version_info < (3, 6):
        print_error(f"Python 3.6 or higher is required. Current version: {sys.version}")
        return False
    
    # Check internet connectivity
    try:
        requests.head("https://cupcake.shiiyu.moe", timeout=5)
    except Exception:
        print_error("Cannot connect to SkyCrypt API. Please check your internet connection.")
        return False
    
    return True

def main() -> None:
    """Main execution function."""
    
    parser = argparse.ArgumentParser(
        description="Extract complete Hypixel SkyBlock profile data for AI analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('username', nargs='?', help='Minecraft username to extract data for')
    parser.add_argument('-p', '--profile', help='Specific profile name to extract')
    parser.add_argument('-s', '--silent', action='store_true', help='Run in silent mode')
    parser.add_argument('-v', '--version', action='version', version=f'SkyBlock Profile Extractor {VERSION}')
    
    args = parser.parse_args()
    
    try:
        print_header(f"SkyBlock Profile Extractor v{VERSION}", args.silent)
        
        # Test prerequisites
        if not test_prerequisites():
            sys.exit(1)
        
        # Get username
        username = args.username
        if not username:
            if args.silent:
                print_error("Username is required in silent mode!")
                sys.exit(1)
            username = input("Enter your Minecraft username: ").strip()
            if not username:
                print_error("Username is required!")
                sys.exit(1)
        
        # Get player UUID
        player_info = get_player_uuid(username, args.silent)
        if not player_info:
            sys.exit(1)
        
        # Get profiles
        profiles = get_player_profiles(player_info['uuid'], username, args.silent)
        if not profiles:
            sys.exit(1)
        
        # Select profile
        selected_profile = select_profile(profiles, args.profile, args.silent)
        if not selected_profile:
            print_error("No profile selected!")
            sys.exit(1)
        
        # Create output directory
        output_dir = create_output_directory(username, selected_profile['profile_cute_name'])
        if not output_dir:
            sys.exit(1)
        
        # Extract data
        results = extract_profile_data(
            player_info['uuid'], 
            selected_profile['profile_id'], 
            output_dir, 
            args.silent
        )
        
        # Show summary
        show_summary(results, output_dir, username, args.silent)
        
        print_success("SkyBlock Profile extraction completed successfully!", args.silent)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if not args.silent:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
