# Contributing to SkyBlock Profile Extractor

🎉 Thank you for considering contributing to the SkyBlock Profile Extractor! We are building the most reliable, AI-ready data extraction tool for Hypixel SkyBlock, and we'd love your help.

## 🌟 Ways to Contribute

### 🐛 Bug Reports
- Use the [GitHub Issues](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues) page.
- **Security Note:** Never include your `api_key.txt` or actual API key in bug reports or logs.
- Include your OS, Python/PowerShell version, and the error message.

### 💡 Feature Suggestions
- Open a [GitHub Issue](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues) with the "enhancement" label.
- We focus on **raw data extraction** for AI context. Features that process data (calculating networth, skill averages) are welcome but should generally be optional or separate from the raw data dump.

### 🔧 Code Contributions
- **Official API Focus:** We primarily use `api.hypixel.net`. Avoid using third-party wrappers or scrapers unless absolutely necessary.
- **Cross-Platform Parity:** If you add a feature to the Python script, try to add it to the PowerShell script (and vice versa).

## 🚀 Getting Started

### Prerequisites
- **Git**
- **PowerShell 5.0+** (for Windows development)
- **Python 3.6+** (for Cross-platform development)
- **Hypixel API Key** (Required for v2.0 development)

### Development Setup

1. **Fork the repository**
   Click the "Fork" button on GitHub.

2. **Clone your fork**
   ```bash
   git clone [https://github.com/YOUR-USERNAME/SkyBlock-Profile-Extractor.git](https://github.com/YOUR-USERNAME/SkyBlock-Profile-Extractor.git)
   cd SkyBlock-Profile-Extractor
   ```

3. **Setup Environment**
* **Python:** Install dependencies: `pip install -r requirements.txt`
* **API Key:** Run the script once or manually create `api_key.txt` with your key.
* **⚠️ IMPORTANT:** Ensure `api_key.txt` is in your `.gitignore` before committing anything!


4. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name

```


5. **Make your changes**
* Test your changes against your own SkyBlock profile.
* Ensure the JSON output remains compatible with the expected AI formats.


6. **Submit a Pull Request**
* Push to your fork and click "New Pull Request" on the main repo.



## 📋 Coding Standards

### Security First 🔒

* **Never commit API keys.** Always read from `api_key.txt`.
* **Sanitize output.** Ensure error messages don't leak sensitive tokens.

### Python (v2.0 Standard)

* Use `requests` for API calls.
* Handle `403 Forbidden` and `429 Too Many Requests` gracefully.
* Use `pathlib` for file handling (OS-agnostic).
* Follow PEP 8 style guidelines.

### PowerShell (v2.0 Standard)

* Support `TLS 1.2` explicitly (required for Hypixel API).
* Use `Invoke-RestMethod` for API calls.
* Implement rate limiting (sleep between requests).
* Keep the `Silent` parameter functional for automation.

## 🧪 Testing

Before submitting a PR, please verify:

1. **Prerequisites Check:** Does the script correctly identify missing API keys or network issues?
2. **Profile Switching:** Can the script handle users with multiple profiles (e.g., Bingo, Ironman)?
3. **Data Integrity:** Are `complete_profile.json` and `bazaar_prices.json` generated correctly?
4. **Clean Exit:** Does the script exit cleanly on `CTRL+C` or fatal errors?

##📁 Project Structure

```text
SkyBlock-Profile-Extractor/
├── README.md              # Documentation & Quick Start
├── CONTRIBUTING.md        # This file
├── LICENSE                # MIT License
├── extract-profile.ps1    # Primary Windows Script (Official API)
├── extract_profile.py     # Primary Python Script (Official API)
├── requirements.txt       # Python dependencies
├── .gitignore             # Ignores api_key.txt and output folders
└── docs/                  # Additional documentation

```

## 🏷️ Commit Message Guidelines

Please use clear, descriptive commit messages:

* `Feat: Add support for Museum data extraction`
* `Fix: Handle API timeout during Bazaar fetch`
* `Docs: Update usage examples in README`
* `Refactor: Optimize JSON saving routine`

## 📜 Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). Please be respectful and inclusive.

---

**Happy Coding!** 🚀
If you have questions, check the [Discussions](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/discussions) tab.
