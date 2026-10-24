# Contributing to SkyBlock Profile Extractor

Thank you for contributing! Our goal is to maintain a reliable, policy-compliant, open-source data extraction utility for Hypixel SkyBlock.

---

## Code of Conduct & Policies

- **Hypixel Policy Compliance**: We strictly adhere to the official [Hypixel Developer Policies](https://developer.hypixel.net/policies/). Contributions introducing continuous player polling, background scraping, or unauthenticated proxies will be rejected.
- **Security Invariant**: Never commit API keys, personal credentials, or authorization headers. Ensure all errors sanitize key material.

---

## Ways to Contribute

### 1. Bug Reports
- Open a ticket at [GitHub Issues](https://github.com/sizwinz/Hypixel-SkyBlock-Profile-Extractor/issues).
- Include operating system, Python version, error logs, and reproduction steps.
- **Never include raw API keys in issue descriptions or stack traces.**

### 2. Feature Suggestions
- Open an Issue with the `enhancement` label.
- Focus on extracting legitimate data available through supported endpoints without mass collection.

### 3. Code Contributions
- **API Version**: Target `https://api.hypixel.net/v2` exclusively. Use HTTP header authentication (`API-Key`).
- **Cross-Platform Parity**: If a new endpoint or feature is added to `extractor.py`, implement corresponding support in `extract-profile.ps1` and `app.py`.
- **Test-Driven Development**: Every new behavior, bug fix, or endpoint integration must include unit tests in `tests/`.

---

## Development Setup

1. **Fork & Clone**
   ```bash
   git clone https://github.com/sizwinz/Hypixel-SkyBlock-Profile-Extractor.git
   cd Hypixel-SkyBlock-Profile-Extractor
   ```

2. **Environment & Dependencies**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate

   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. **Running the Test Suite**
   ```bash
   pytest -v
   ```

4. **Local API Key**
   - Place your development key into `api_key.txt` (excluded in `.gitignore`) or set the `HYPIXEL_API_KEY` environment variable.

---

## Architecture & Project Structure

```text
├── api_client.py          # HTTP requests, API-Key header auth, retries, and error handling
├── profile_service.py     # Mojang UUID resolution and profile normalization
├── extractor.py           # Resilient endpoint orchestration across categories
├── analysis.py            # Deterministic progression metrics and recommendations
├── exporter.py            # JSON serialization, SHA-256 manifests, and in-memory ZIP generation
├── app.py                 # Streamlit graphical interface
├── extract_profile.py     # Backwards-compatible Python CLI
├── extract-profile.ps1    # Native Windows PowerShell utility
├── API_USAGE.md           # Hypixel API v2 architecture and compliance documentation
├── PERSONAL_API_APPLICATION.md # Suggested re-application draft for Hypixel Developer Dashboard
├── requirements.txt       # Production dependencies (requests, streamlit)
├── requirements-dev.txt   # Development dependencies (pytest, responses)
├── pyproject.toml         # Build system and pytest configuration
└── tests/                 # Automated test suite
    ├── test_api_client.py
    ├── test_profile_service.py
    ├── test_extractor.py
    ├── test_analysis.py
    ├── test_exporter.py
    └── test_cli.py
```

---

## Coding Standards

### General
- Write self-documenting code with clear type annotations.
- Avoid redundant comments for standard code; document complex domain logic and security invariants only.
- Redact credentials dynamically from error strings and representation methods.

### Python
- Follow PEP 8 guidelines.
- Use `requests.Session` for connection pooling.
- Use `pathlib.Path` for filesystem operations.
- Raise domain-specific exceptions inheriting from `SkyBlockExtractorError`. Never call `sys.exit()` in library modules.

### PowerShell
- Enforce TLS 1.2: `[Net.ServicePointManager]::SecurityProtocol`.
- Maintain `-Depth 100` for JSON serialization to avoid truncating deep API structures.
- Support both dashed and undashed UUID keys when querying member dictionaries.

---

## Commit Guidelines

Follow conventional commit formats:
- `feat: add items endpoint schema extraction`
- `fix: resolve rate limit backoff timing on HTTP 429`
- `docs: update API compliance checklist`
- `test: add unit coverage for Catacombs XP calculation`
