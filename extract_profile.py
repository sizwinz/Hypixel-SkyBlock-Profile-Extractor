import requests
import json
import os
import time
import sys
from datetime import datetime
from pathlib import Path
import argparse

# Configuration
VERSION = "2.0"
HYPIXEL_API_URL = "https://api.hypixel.net"
MOJANG_API_URL = "https://api.mojang.com"
USER_AGENT = f"SkyBlock-Profile-Extractor/{VERSION}"
TIMEOUT = 30

# Colors for terminal output
class Colors:
    HEADER = '\033[96m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    INFO = '\033[94m'
    ACCENT = '\033[95m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.HEADER}>> {title}{Colors.END}")
    print(f"{Colors.HEADER}{'-' * 50}{Colors.END}")

def print_success(msg):
    print(f"{Colors.SUCCESS}[✓] {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.INFO}[i] {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.WARNING}[!] {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.ERROR}[✗] {msg}{Colors.END}")

# --- API Key Handling ---

def get_api_key(silent=False):
    """Load API key from file or prompt user."""
    key_file = Path("api_key.txt")
    
    if key_file.exists():
        try:
            key = key_file.read_text().strip()
            if len(key) > 30:
                if not silent: print_info("Loaded API key from api_key.txt")
                return key
        except Exception:
            pass

    if silent:
        print_error("API Key not found in api_key.txt (Required for silent mode)")
        sys.exit(1)

    print_warning("Hypixel API Key not found!")
    print("  1. Go to https://developer.hypixel.net")
    print("  2. Login and copy your 'Development Key'")
    
    while True:
        key = input(f"\n{Colors.ACCENT}Enter your Hypixel API Key: {Colors.END}").strip()
        if len(key) > 30:
            try:
                key_file.write_text(key)
                print_success("API Key saved to api_key.txt")
                return key
            except Exception as e:
                print_error(f"Could not save API key: {e}")
                return key
        print_error("Invalid API Key format. Please try again.")

# --- API Calls ---

def invoke_mojang_api(endpoint):
    try:
        resp = requests.get(f"{MOJANG_API_URL}/{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise Exception(f"Mojang API Error: {e}")

def invoke_hypixel_api(endpoint, api_key, params=None):
    if params is None: params = {}
    params['key'] = api_key
    
    headers = {'User-Agent': USER_AGENT}
    
    try:
        resp = requests.get(f"{HYPIXEL_API_URL}/{endpoint}", params=params, headers=headers, timeout=TIMEOUT)
        data = resp.json()
        
        if not data.get('success'):
            raise Exception(f"API Error: {data.get('cause', 'Unknown error')}")
        
        return data
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            raise Exception("403 Forbidden - Invalid API Key")
        raise Exception(f"HTTP Error: {e}")
    except Exception as e:
        raise Exception(str(e))

# --- Core Logic ---

def get_player_uuid(username):
    print_info(f"Looking up UUID for '{username}'...")
    try:
        data = invoke_mojang_api(f"users/profiles/minecraft/{username}")
        if 'id' in data:
            # Format UUID with dashes
            raw_uuid = data['id']
            formatted_uuid = f"{raw_uuid[:8]}-{raw_uuid[8:12]}-{raw_uuid[12:16]}-{raw_uuid[16:20]}-{raw_uuid[20:]}"
            print_success(f"Found player: {data['name']}")
            return formatted_uuid, raw_uuid
        raise Exception("Player not found")
    except Exception as e:
        print_error(f"UUID Lookup Failed: {e}")
        sys.exit(1)

def get_profiles(uuid, api_key):
    print_info("Fetching SkyBlock profiles...")
    try:
        data = invoke_hypixel_api("skyblock/profiles", api_key, {'uuid': uuid})
        if not data.get('profiles'):
            raise Exception("No SkyBlock profiles found for this user.")
        
        profiles = []
        for p in data['profiles']:
            # Determine last_save for sorting
            member = p['members'].get(uuid.replace('-', ''), {})
            last_save = member.get('last_save', 0)
            
            profiles.append({
                'id': p['profile_id'],
                'name': p.get('cute_name', 'Unknown'),
                'game_mode': p.get('game_mode', 'normal'),
                'last_save': last_save,
                'data': p
            })
        
        # Sort by last played (descending)
        profiles.sort(key=lambda x: x['last_save'], reverse=True)
        return profiles
    except Exception as e:
        print_error(f"Profile Fetch Failed: {e}")
        sys.exit(1)

def select_profile(profiles, requested_name=None, silent=False):
    if requested_name:
        for p in profiles:
            if p['name'].lower() == requested_name.lower():
                print_success(f"Selected profile: {p['name']}")
                return p
        print_warning(f"Profile '{requested_name}' not found.")

    if silent or len(profiles) == 1:
        print_info(f"Auto-selecting most recent profile: {profiles[0]['name']}")
        return profiles[0]

    print(f"\n{Colors.INFO}Available Profiles:{Colors.END}")
    for i, p in enumerate(profiles):
        mode = f" [{p['game_mode'].upper()}]" if p['game_mode'] != 'normal' else ""
        print(f"  {i+1}. {p['name']}{mode}")

    while True:
        choice = input(f"\nSelect profile [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(profiles):
            return profiles[int(choice)-1]

def extract_data(uuid, profile, api_key, username):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"SkyBlock_{username}_{profile['name']}_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print_header("Starting Data Extraction")
    print_info(f"Output Directory: {output_dir}")

    extracted_files = []

    # 1. Save Complete Profile (The Holy Grail)
    try:
        print_info("Saving complete profile data...")
        with open(output_dir / "complete_profile.json", 'w', encoding='utf-8') as f:
            json.dump(profile['data'], f, indent=4)
        print_success("Saved complete_profile.json")
        extracted_files.append("complete_profile.json")
    except Exception as e:
        print_error(f"Failed to save profile: {e}")

    # 2. Auxiliary Data Points
    endpoints = [
        ("player", {'uuid': uuid}, "player_data.json", "Global Player Stats"),
        ("skyblock/bingo", {'uuid': uuid}, "bingo_data.json", "Bingo Data"),
        ("skyblock/bazaar", {}, "bazaar_prices.json", "Bazaar Prices"),
        ("skyblock/auctions", {'profile': profile['id']}, "active_auctions.json", "Active Auctions"),
        ("skyblock/news", {}, "skyblock_news.json", "SkyBlock News")
    ]

    for ep, params, filename, desc in endpoints:
        try:
            print_info(f"Fetching {desc}...")
            data = invoke_hypixel_api(ep, api_key, params)
            with open(output_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print_success(f"Saved {filename}")
            extracted_files.append(filename)
        except Exception as e:
            print_warning(f"Skipped {desc}: {e}")

    # 3. Generate Report
    readme_text = f"""
SKYBLOCK PROFILE EXTRACTION REPORT
===================================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Player: {username}
Profile: {profile['name']} [{profile['game_mode']}]
UUID: {uuid}

FILES EXTRACTED:
----------------
{chr(10).join(f"- {f}" for f in extracted_files)}

IMPORTANT:
1. 'complete_profile.json' contains ALL raw data (Inventories, Skills, Collections, etc.).
2. Data extracted via Official Hypixel API.
3. Upload these files to AI tools for analysis.
"""
    (output_dir / "README.txt").write_text(readme_text, encoding='utf-8')
    
    return output_dir, len(extracted_files)

def main():
    parser = argparse.ArgumentParser(description="Hypixel SkyBlock Profile Extractor v2.0")
    parser.add_argument('username', nargs='?', help="Minecraft Username")
    parser.add_argument('-p', '--profile', help="Specific profile name")
    parser.add_argument('-s', '--silent', action='store_true', help="Run without interaction")
    args = parser.parse_args()

    print_header(f"SkyBlock Extractor v{VERSION}")

    # 1. Get API Key
    api_key = get_api_key(args.silent)

    # 2. Get Username
    username = args.username
    if not username:
        if args.silent:
            print_error("Username required in silent mode")
            sys.exit(1)
        username = input(f"Enter Minecraft Username: ").strip()

    # 3. Get UUID & Profiles
    uuid_formatted, uuid_raw = get_player_uuid(username)
    profiles = get_profiles(uuid_formatted, api_key)

    # 4. Select Profile
    selected = select_profile(profiles, args.profile, args.silent)

    # 5. Extract
    output_dir, count = extract_data(uuid_formatted, selected, api_key, username)

    # 6. Summary
    print_header("Extraction Complete")
    print(f"{Colors.SUCCESS}Successfully extracted {count} files to:{Colors.END}")
    print(f"{Colors.ACCENT}{output_dir}{Colors.END}")
    print(f"\n{Colors.INFO}Next Steps:{Colors.END}")
    print("1. Zip the folder.")
    print("2. Upload 'complete_profile.json' and 'bazaar_prices.json' to ChatGPT/Claude.")
    print("3. Ask: 'Analyze my networth and suggest progression steps.'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)
