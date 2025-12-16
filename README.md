# 🚀 SkyBlock Profile Extractor

> **Extract your complete Hypixel SkyBlock profile data securely via the Official API.**

Get raw, comprehensive data from your SkyBlock profile for AI analysis, personal tracking, or data visualization. This tool uses the **Official Hypixel API** to ensure 100% reliability and zero blocking issues.

[![GitHub stars](https://img.shields.io/github/stars/Sahaj33-op/Hypixel-SkyBlock-Profile-Extractor?style=social)](https://github.com/Sahaj33-op/Hypixel-SkyBlock-Profile-Extractor/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?logo=powershell&logoColor=white)](https://docs.microsoft.com/en-us/powershell/)

## ✨ Features

- 🛡️ **Official API Integration** - Uses `api.hypixel.net` for maximum stability (No more 403 Forbidden errors!)
- 🔐 **Secure Key Storage** - Asks for your API key once and stores it locally (`api_key.txt`)
- 🤖 **AI-Ready Format** - Exports massive JSON datasets perfect for LLM (ChatGPT/Claude) analysis
- 📦 **Complete Data Dump** - Fetches Profiles, Inventories, Bazaar Prices, Auctions, and Bingo data
- ⚡ **Smart Caching** - Respects rate limits while fetching data fast

## 🎮 What Data You'll Get

Unlike website scrapers, this tool pulls **raw data** directly from Hypixel servers:

### 📁 Primary Data
- **`complete_profile.json`**: The holy grail. Contains **everything** nested inside:
  - 🎒 **Inventories**: Main, Armor, Ender Chest, Sacks, Vault, Wardrobe, Fishing Bag, Potion Bag
  - ⚔️ **Progression**: Skills, Slayers, Dungeons, Collections, Crimson Isle, Rift
  - 🐾 **Content**: Pets, Minions, Accessories, Museum, Garden

### 🌍 World Data (Context for AI)
- **`bazaar_prices.json`**: Current market prices for all items (crucial for networth calculation)
- **`active_auctions.json`**: Real-time auction house data for your profile
- **`player_data.json`**: Global account stats (Karma, Network Level, Ranks)
- **`skyblock_news.json`**: Latest patch notes and updates

## 🚀 Quick Start

### 📋 Prerequisites

1. **Enable API Access in SkyBlock** (Required!):
   - Join Hypixel SkyBlock
   - Right-click the **Nether Star** (SkyBlock Menu)
   - Click **Redstone Torch** (Settings)
   - Click **Comparator** (API Settings)
   - **Enable ALL options** (Skills, Inventory, Collections, Vault, etc.)
   - Wait 5-10 minutes for changes to take effect

### Option 1: PowerShell (Windows - Recommended)

```powershell
# Download and run the extractor
iwr -Uri "https://raw.githubusercontent.com/Sahaj33-op/SkyBlock-Profile-Extractor/main/extract-profile.ps1" -OutFile "extract-profile.ps1"
.\extract-profile.ps1
```

### Option 2: Python (Cross-Platform)

```bash
# Clone the repository
git clone https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor.git
cd SkyBlock-Profile-Extractor

# Install requirements
pip install -r requirements.txt

# Run the extractor
python extract_profile.py
```

### Option 3: Direct Download

1. Download `extract-profile.ps1` or `extract_profile.py` from this repository
2. Run the script
3. Enter your Minecraft username when prompted
4. Wait for extraction to complete

## 📋 Usage Example

```
.\hypixel-extract.ps1
```

## **First Run Setup**:
* Enter your Minecraft Username.
* When prompted, paste your **Hypixel API Key** (from Prerequisite #1).
* The key is saved securely to `api_key.txt` for future runs.



## 📁 Output Structure

Data is saved in a timestamped folder: `SkyBlock_Username_ProfileName_YYYYMMDD_HHMMSS/`

```text
SkyBlock_Sahaj33_Tomato_20251216/
├── 📄 complete_profile.json   <-- GIVE THIS TO AI (Contains 90% of your data)
├── 📄 player_data.json        <-- Account stats
├── 📄 bazaar_prices.json      <-- Economy context
├── 📄 active_auctions.json    <-- Your auctions
└── 📄 README.txt              <-- Report summary

```

## 🤖 AI Analysis Examples

Since you are providing raw API data, you can ask powerful questions to ChatGPT or Claude. **Upload `complete_profile.json` and `bazaar_prices.json`** and ask:

### 💰 Networth & Economy

> "Using the `bazaar_prices.json` as a reference, calculate the approximate liquid value of the contents in my `inv_contents` and `ender_chest_contents` found in `complete_profile.json`."

### ⚔️ Gear Optimization

> "Analyze my `inv_armor` and `equipment_contents` in `complete_profile.json`. Based on my Dungeon classes (catacombs data), what accessories or upgrades am I missing?"

### 📈 Skill Grinding

> "Look at my mining data in `complete_profile.json`. Which HotM (Heart of the Mountain) perks should I prioritize to improve my gemstone rates?"

## 🛠️ Troubleshooting

### Common Issues

**❌ "403 Forbidden" Error**
- ✅ **Solution**: Enable API access in SkyBlock settings and wait 10 minutes

**❌ "Profile not found"**  
- ✅ **Solution**: Check username spelling and ensure you have SkyBlock profiles

**❌ "Connection timeout"**
- ✅ **Solution**: Check internet connection and try again

**❌ Script won't run**
- ✅ **Solution**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned` in PowerShell

### Need Help?

- 🐛 [Report Issues](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues)
- 💬 [Join Discussions](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/discussions)
- 📖 [Check Wiki](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/wiki)

## 🤝 Contributing

We welcome contributions!

* 🐛 Report bugs
* 💡 Suggest features
* 🔧 Submit Pull Requests

**Note for Contributors**: Please add `api_key.txt` to your `.gitignore` to prevent leaking your credentials.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE]() file for details.

## ⭐ Support the Project

If this tool helped you, please:
- ⭐ Star this repository
- 🐦 Share it with friends
- 🐛 Report any issues
- 💡 Suggest improvements

## 🙏 Acknowledgments

- 🎮 **Hypixel Network** - For creating SkyBlock
- 🔗 **SkyCrypt Team** - For providing the excellent API
- 👥 **SkyBlock Community** - For feedback and suggestions
- 🤖 **AI Community** - For inspiring data-driven gameplay

---

<div align="center">

**Made with ❤️ for the SkyBlock community**

[⭐ Star](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor) • [🐛 Report Bug](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues) • [💡 Request Feature](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues)

</div>
