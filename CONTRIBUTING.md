# Contributing to SkyBlock Profile Extractor

Thank you for contributing! We aim to build a reliable, AI-ready data extraction tool for Hypixel SkyBlock.

## Ways to Contribute

### Bug Reports
- Use [GitHub Issues](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues).
- **Security:** Never include your `api_key.txt` or actual API key.
- Include OS, Python/PowerShell version, and error logs.

### Feature Suggestions
- Open an Issue with the "enhancement" label.
- Focus on **raw data extraction** (getting the data out) rather than data processing (calculating averages).

### Code Contributions
- **API Version:** We strictly use `api.hypixel.net/v2`.
- **Parity:** If you add a feature ("Mining Data") to `extract_profile.py`, please also add it to `extract-profile.ps1`.

## Development Setup

1. **Fork & Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/SkyBlock-Profile-Extractor.git
   cd SkyBlock-Profile-Extractor
   ```

2. **Environment**
   - **Python:** `pip install requests`
   - **PowerShell:** No install needed (Win 10+).

3. **API Key**
   - Create `api_key.txt` in the root.
   - Paste your key inside.
   - **Check .gitignore** to ensure this file is never committed.

## Coding Standards

### General
- **Security:** Never commit keys. Sanitize errors.
- **Reliability:** Handle HTTP 429 (Rate Limit) and 403 (Invalid Key).

### Python
- Use `requests` library.
- Use `pathlib` for paths.
- Follow PEP 8.

### PowerShell
- Enforce TLS 1.2: `[Net.ServicePointManager]::SecurityProtocol`
- Use `Invoke-RestMethod`.
- Handle dynamic properties (v2 API responses) with correct quoting: `$obj."$uuid"`.

## Project Structure

```text
├── README.md              # Documentation
├── extract-profile.ps1    # Main Windows Script
├── extract_profile.py     # Main Python Script
├── .gitignore             # Ignores secrets & output
└── api_key.txt            # Your local key (ignored)
```

## Commit Guidelines

- `Feat: Add Museum endpoint`
- `Fix: specific auction filtering`
- `Docs: Update prerequisites`

Happy Coding!
