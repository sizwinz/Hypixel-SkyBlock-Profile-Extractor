# Hypixel API v2 Architecture & Policy Compliance

## 1. Project Overview

SkyBlock Profile Extractor is an open-source, non-monetized, client-side utility built in Python and PowerShell. It enables individual Minecraft players to export and inspect their own Hypixel SkyBlock profile data and economy snapshots on demand.

The project does not offer automated background polling, mass data harvesting, or continuous player tracking. Every API interaction is strictly initiated by explicit user command.

---

## 2. Technical Architecture

The extraction pipeline consists of decoupled components:

- **HTTP Client Layer (`api_client.py`)**: Interacts with Mojang and Hypixel API v2 endpoints via `requests.Session`. Enforces HTTP header authentication (`API-Key`), handles status codes, and implements backoff on rate limits.
- **Profile Discovery & Normalization (`profile_service.py`)**: Resolves player UUIDs, normalizes member dictionaries (supporting both dashed and undashed UUID formatting), and sorts profiles by recent activity.
- **Extraction Orchestrator (`extractor.py`)**: Executes requests across requested categories. Isolates endpoint failures so partial failures do not prevent remaining categories from completing.
- **Progression Analyzer (`analysis.py`)**: Calculates deterministic skill levels, slayer milestones, catacombs progression, and explainable next-step recommendations from exported data.
- **Serialization & Manifest Engine (`exporter.py`)**: Writes timestamped JSON datasets, generates `extraction_manifest.json` with SHA-256 file hashes, and streams in-memory ZIP packages.
- **Presentation Interfaces**:
  - Web UI: Streamlit application (`app.py`) with real-time extraction progress and in-memory browser downloads.
  - Command-Line Utility: Standalone Python CLI (`extract_profile.py`).
  - Windows PowerShell Utility: Standalone PowerShell script (`extract-profile.ps1`).

---

## 3. Endpoints & Request Specifications

All Hypixel requests target the official v2 base path: `https://api.hypixel.net/v2`.

| Endpoint Path | Method | Authentication | Query Parameters | Data Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `skyblock/profiles` | GET | `API-Key` Header | `uuid=<player_uuid>` | Enumerate SkyBlock profiles for target player |
| `skyblock/profile` | GET | `API-Key` Header | `profile=<profile_id>` | Detailed profile member stats and inventories |
| `player` | GET | `API-Key` Header | `uuid=<player_uuid>` | Global player stats and achievement data |
| `skyblock/garden` | GET | `API-Key` Header | `profile=<profile_id>` | Farming levels, visitor milestones, plot upgrades |
| `skyblock/museum` | GET | `API-Key` Header | `profile=<profile_id>` | Donated museum items, value appraisals |
| `guild` | GET | `API-Key` Header | `player=<player_uuid>` | Guild rank, roster, and guild level |
| `recentgames` | GET | `API-Key` Header | `uuid=<player_uuid>` | Recent minigame session list |
| `status` | GET | `API-Key` Header | `uuid=<player_uuid>` | Current online/offline player status |
| `skyblock/firesales` | GET | `API-Key` Header | None | Active community cosmetics fire sales |
| `skyblock/bingo` | GET | `API-Key` Header | `uuid=<player_uuid>` | Community bingo event progress |
| `skyblock/bazaar` | GET | `API-Key` Header | None | Live market buy/sell order book snapshot |
| `skyblock/auction` | GET | `API-Key` Header | `profile=<profile_id>` | Active auction listings for target profile |
| `skyblock/news` | GET | `API-Key` Header | None | In-game announcements and update logs |
| `resources/skyblock/items` | GET | None (Public Keyless) | None | Official SkyBlock item schema and registry definitions |
| `resources/skyblock/skills` | GET | None (Public Keyless) | None | Official SkyBlock skill level thresholds and descriptions |
| `resources/skyblock/collections` | GET | None (Public Keyless) | None | Official SkyBlock collection categories and tier thresholds |

---

## 4. Credential Handling & Security Practices

- **Header Authentication**: As mandated by Hypixel Developer policies, the API key is passed strictly via the `API-Key` HTTP header. URL query parameter transmission (`?key=...`) is prohibited.
- **No Embedded Credentials**: The codebase contains zero developer credentials, tokens, or hardcoded secrets.
- **Local Secret Isolation**: Keys are stored locally in an untracked `api_key.txt` file or supplied via the `HYPIXEL_API_KEY` environment variable. Both `.env` and `api_key.txt` are included in `.gitignore`.
- **Credential Redaction**: `HypixelAPIClient.redact_api_key()` dynamically scrubs the user's API key from exception messages, representation strings, terminal logs, and exported files.

---

## 5. Rate Limiting & Concurrency Policies

- **Interactive Execution Only**: Extractions execute sequentially on user demand. No scheduled jobs, background workers, or daemon services exist.
- **HTTP 429 Resilience**: When an HTTP 429 response is encountered, the client parses the `RateLimit-Reset` header, applies bounded exponential backoff with random jitter, and retries the request up to configured retry limits.
- **In-Memory TTL Caching**: Static resource endpoints (such as `resources/skyblock/items`) and global catalog snapshots (such as Bazaar prices and active fire sales) are cached in-memory with appropriate TTLs to eliminate duplicate calls without tracking players.
- **Request Pacing**: The standalone Windows PowerShell utility includes configurable request delays (`$Script:RateLimitMs = 500`) to remain well within personal quota limits.
- **Timeout Enclosure**: All HTTP requests enforce an explicit network timeout (default: 30 seconds) to prevent hanging threads.

---

## 6. Hypixel Developer Policy Compliance Matrix

| Policy Dimension | Project Implementation & Guarantees |
| :--- | :--- |
| **No Mass Data Scraping** | The tool queries data strictly for a single player/profile per invocation. Batch user processing is not supported. |
| **No Continuous Player Tracking** | No database exists. The software records a single point-in-time snapshot and disconnects. |
| **No Public API Proxy** | The software does not provide an intermediate API gateway or broker requests for third-party tools. |
| **Non-Monetized & Free** | Fully open source under the MIT License without paywalls, ads, donations, or subscription gates. |
| **Non-Affiliation Notice** | Prominently stated in `README.md`, `app.py`, CLI banners, and exported reports: "Not affiliated with or endorsed by Hypixel Inc." |
| **Player Privacy Respect** | Transparently detects and reports when player in-game API settings (inventory, skills, banking) are toggled off. |
