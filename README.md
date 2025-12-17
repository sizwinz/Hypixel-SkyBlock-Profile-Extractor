# SkyBlock Profile Extractor

**Extract complete Hypixel SkyBlock profile data securely via the Official API.**

This tool fetches raw, comprehensive data from SkyBlock profiles for analysis, tracking, or data visualization. It uses the Official Hypixel API v2 for reliability.

## Features

Retrieves the following data points:
- **Complete Profile**: Inventories, Skills, Slayers, Dungeons, Collections, Vault, Wardrobe, Equipment.
- **Garden Data**: Farming stats, plot upgrades, and visitors.
- **Museum Data**: Donated items, appraisals, and special items.
- **Guild Data**: Guild details, ranks, and members.
- **Recent Games**: Match history for non-SkyBlock games.
- **Online Status**: Current online status and server.
- **Economy**: Active Auctions and Bazaar Prices.
- **Misc**: Player Stats, Fire Sales, News.

## Quick Start

### Prerequisites
1. **Hypixel API Key**: obtained from the [Hypixel Developer Dashboard](https://developer.hypixel.net).
2. **SkyBlock API Access**: Enabled in-game via SkyBlock Menu -> Settings (Redstone Torch) -> API Settings (Comparator).

### Usage

**PowerShell (Windows)**
```powershell
.\extract-profile.ps1
```

**Python (Cross-Platform)**
```bash
pip install requests
python extract_profile.py
```

On the first run, you will be prompted to enter your Minecraft username and API key. The key is saved locally to `api_key.txt`.

## Output

Data is saved in a timestamped directory: `SkyBlock_<Username>_<Profile>_<Timestamp>/`.

### Key Files
- `complete_profile.json`: Contains the majority of player data (inventory, skills, progression).
- `garden_data.json`: Detailed Garden and farming statistics.
- `museum_data.json`: Museum collection data.
- `bazaar_prices.json`: Current market data for economy analysis.

## AI Analysis

For analysis using LLMs (ChatGPT, Claude), upload `complete_profile.json` and `bazaar_prices.json` to the model and provide a prompt.

**Example Prompt:**
> "Analyze the `inv_contents` and `ender_chest_contents` in `complete_profile.json`. Using `bazaar_prices.json` as a reference, estimate the total liquid value of these items."

---
*Not affiliated with Hypixel.*
