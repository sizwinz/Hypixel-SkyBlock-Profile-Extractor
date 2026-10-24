# Suggested Hypixel Personal API Application Draft

> [!NOTE]
> Review and copy the contents below into the official Hypixel Developer Dashboard application form at [developer.hypixel.net](https://developer.hypixel.net/). Do not submit automated applications.

---

## 1. Basic Project Details

- **Project Name:** SkyBlock Profile Extractor
- **Project Type:** Personal Project / Open-Source Utility
- **Project URL:** https://github.com/sizwinz/Hypixel-SkyBlock-Profile-Extractor
- **Target Tier:** Personal API Key

---

## 2. Project Description

SkyBlock Profile Extractor is a free, non-monetized, open-source utility designed for personal Hypixel SkyBlock players. It allows players to extract their own character data, inventory states, and progression statistics directly into structured JSON files for offline analysis and personal record-keeping.

The tool provides:
1. A lightweight web interface (`streamlit run app.py`) with real-time extraction progress and in-browser ZIP exports.
2. A command-line Python script (`extract_profile.py`) for scripted personal backups.
3. A native Windows PowerShell script (`extract-profile.ps1`).
4. A deterministic progression analyzer that summarizes skill averages, slayer milestones, and catacombs levels.

---

## 3. Endpoints Requested & Justification

All requests use the official Hypixel API v2 (`https://api.hypixel.net/v2`) with HTTP header authentication (`API-Key`):

- `v2/skyblock/profiles` & `v2/skyblock/profile`: Used to enumerate and fetch player profile member statistics and inventories.
- `v2/player`: Used to retrieve base player achievements and network levels.
- `v2/skyblock/garden`: Used to review personal farming milestones, plot unlocks, and visitor statistics.
- `v2/skyblock/museum`: Used to catalog donated items and collection appraisals.
- `v2/guild`: Used to display guild membership information.
- `v2/skyblock/bazaar` & `v2/skyblock/auction`: Used to capture market pricing context for inventory review.
- `v2/skyblock/news` & `v2/skyblock/firesales`: Used to inspect community event and update logs.
- `v2/resources/skyblock/items`, `v2/resources/skyblock/skills`, `v2/resources/skyblock/collections`: Keyless public resource endpoints used to map official item schemas, skill milestones, and collection definitions without authenticating.

---

## 4. Expected Request Volume & Pacing

- **Volume:** Low, on-demand traffic. A complete extraction sequence makes approximately 10 to 13 HTTP requests.
- **Trigger:** Initiated exclusively by manual user action.
- **Frequency:** Typical personal use is 1 to 3 times per week when reviewing gear or skill milestones.
- **Concurrency & Resilience:** Sequential requests. The Python engine implements bounded exponential backoff on HTTP 429 using `RateLimit-Reset` and in-memory TTL caching for static catalog data. The PowerShell utility includes paced delay (`$Script:RateLimitMs = 500`).
- **Prohibited Patterns:** No continuous player tracking, no automated cron jobs, no background scraping, and no mass database collection.

---

## 5. Security & Credential Storage

- **Storage:** The API key is stored locally on the user's personal machine in `api_key.txt` or passed via the `HYPIXEL_API_KEY` environment variable.
- **Git Safety:** Secret files (`api_key.txt`, `.env`) are excluded in `.gitignore`. No keys are committed to Git.
- **Redaction:** The client codebase dynamically redacts API keys from logs, exception messages, and exported files.
- **Header Auth:** Keys are transmitted solely via the `API-Key` HTTP header.

---

## 6. Addressing Previous Application Feedback

The previous application was rejected because the repository link was inaccessible. This re-application provides:
- A fully accessible, public repository URL: `https://github.com/sizwinz/Hypixel-SkyBlock-Profile-Extractor`.
- Step-by-step setup documentation in `README.md`.
- Automated test coverage in `tests/` with continuous integration.
- Dedicated architectural and policy documentation in `API_USAGE.md`.
