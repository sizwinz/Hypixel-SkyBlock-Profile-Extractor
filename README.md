# 🚀 SkyBlock Profile Extractor

> **Extract your complete Hypixel SkyBlock profile data in seconds!**

Get every stat, item, skill, and progression detail from your SkyBlock profile for AI analysis, personal tracking, or data visualization. Works seamlessly with the SkyCrypt API.

[![GitHub stars](https://img.shields.io/github/stars/Sahaj33-op/SkyBlock-Profile-Extractor?style=social)](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PowerShell](https://img.shields.io/badge/PowerShell-5391FE?logo=powershell&logoColor=white)](https://docs.microsoft.com/en-us/powershell/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://python.org)

## ✨ Features

- 🎯 **Complete Profile Data** - Extract every aspect of your SkyBlock profile
- 🤖 **AI-Ready Format** - Perfect JSON format for ChatGPT, Claude, or any LLM analysis
- ⚡ **Lightning Fast** - Get 25+ data files in under 30 seconds
- 🛡️ **Safe & Secure** - Uses official SkyCrypt API, no account credentials needed
- 🎨 **User-Friendly** - Simple one-command execution
- 📊 **Comprehensive Coverage** - Stats, items, skills, dungeons, slayers, and more!

## 🎮 What Data You'll Get

### Core Profile Data
- ⭐ **Complete Statistics** - SkyBlock level, playtime, achievements
- 💰 **Networth Breakdown** - Exact value of every item you own
- 🎯 **All Skills** - Levels, XP, and progression for all 12+ skills
- ⚔️ **Combat Data** - Slayer kills, dungeon runs, bestiary progress

### Inventory & Items
- 🎒 **Complete Inventories** - Main inventory, ender chest, vault, all bags
- ⚔️ **Equipment Analysis** - Current gear, weapons, accessories
- 🐾 **Pet Collection** - All pets, levels, and candy usage
- 🤖 **Minion Data** - Automation setup and production stats

### Progression Tracking
- 📚 **Collections** - Progress on all 200+ collections
- 🌋 **Area Progress** - Crimson Isle, Rift, Garden, and more
- 🏆 **Achievements** - Completed and remaining goals
- 💎 **Rare Items** - Special items and their locations

## 🚀 Quick Start

### Prerequisites

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

```powershell
PS C:\> .\extract-profile.ps1
🚀 SkyBlock Profile Extractor v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enter your Minecraft username: Sahaj33

🔍 Looking up UUID...
✅ Found player: Sahaj33 (4507b801...)

📋 Available profiles:
  1. 🍅 Tomato (Selected) - SkyBlock Level 42
  2. 🥥 Coconut - SkyBlock Level 15

Select profile [1]: 1

📊 Extracting profile data...
✅ Stats & Overview
✅ Networth Analysis  
✅ Skills & XP
✅ Inventory Contents
✅ Equipment & Gear
... (25 total files)

🎉 Extraction completed!
📁 Data saved to: skyblock_data_20251019_143022
📊 Total files: 25
💾 Total size: 2.3 MB

🤖 Ready for AI analysis!
```

## 📁 Output Structure

Your extracted data will be organized in a timestamped folder:

```
skyblock_data_YYYYMMDD_HHMMSS/
├── 📊 Core Data
│   ├── stats.json              # Complete profile overview
│   ├── networth.json           # Wealth breakdown
│   ├── skills.json             # All skill levels & XP
│   ├── dungeons.json           # Dungeon progress
│   └── slayer.json             # Slayer boss kills
├── 🎒 Inventory Data  
│   ├── inventory_main.json     # Main inventory
│   ├── inventory_enderchest.json
│   ├── inventory_vault.json
│   └── inventory_bags.json
├── ⚔️ Combat & Progression
│   ├── gear.json               # Equipment
│   ├── accessories.json        # Talismans
│   ├── pets.json               # Pet collection
│   └── bestiary.json           # Monster kills
└── 🌟 Special Areas
    ├── crimson_isle.json       # Nether progress
    ├── rift.json               # Rift dimension
    └── garden.json             # Farming data
```

## 🤖 AI Analysis Examples

Once you have your data, you can ask any LLM:

### 📈 Progression Analysis
> "Analyze my SkyBlock profile and tell me what I should focus on next to maximize my progression."

### 💰 Networth Optimization  
> "Look at my inventory and networth data. What items should I sell or buy to increase my coins efficiently?"

### ⚔️ Combat Improvement
> "Based on my gear, stats, and dungeon performance, how can I improve my combat effectiveness?"

### 🎯 Goal Planning
> "What collections am I closest to completing? Create a priority list for my next goals."

## 🔧 Advanced Usage

### Custom Profile Selection

```powershell
# Extract specific profile by name
.\extract-profile.ps1 -Username "YourName" -Profile "Coconut"
```

### Automated Extraction

```powershell
# Silent mode for automation
.\extract-profile.ps1 -Username "YourName" -Silent
```

### Data Analysis Tools

```python
# Load and analyze your data with Python
import json

# Load your profile data
with open('stats.json', 'r') as f:
    stats = json.load(f)

with open('networth.json', 'r') as f:
    networth = json.load(f)

# Analyze your progression
print(f"SkyBlock Level: {stats['stats']['skyblock_level']['level']}")
print(f"Total Networth: {networth['networth']['networth']:,} coins")
```

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

We welcome contributions! Here's how you can help:

- 🐛 Report bugs or issues
- 💡 Suggest new features  
- 📝 Improve documentation
- 🔧 Submit pull requests

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

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