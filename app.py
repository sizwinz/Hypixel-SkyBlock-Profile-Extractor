"""Streamlit Web Application for Hypixel SkyBlock Profile Extraction and Analysis."""

import io
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_src_dir = str(Path(__file__).resolve().parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

import streamlit as st

from skyblock_extractor.api_client import (
    AuthenticationError,
    HypixelAPIClient,
    PlayerNotFoundError,
    ProfileNotFoundError,
    RateLimitExceededError,
    SkyBlockExtractorError,
    can_persist_key_to_disk,
    is_hosted_environment,
    is_streamlit_cloud,
)
from skyblock_extractor.profile_service import normalize_profiles
from skyblock_extractor.extractor import (
    ProfileExtractor,
    ExtractionResult,
    PUBLIC_RESOURCE_SPECS,
    classify_extraction_outcome,
)
from skyblock_extractor.analysis import ProfileAnalyzer
from skyblock_extractor.exporter import ProfileExporter, PublicResourceExporter

APP_VERSION = "2.1.0"


def resolve_server_api_key() -> str:
    """Resolve pre-configured server API key from environment or Streamlit secrets."""
    key = os.environ.get("HYPIXEL_API_KEY", "").strip()
    if not key:
        try:
            if hasattr(st, "secrets") and "HYPIXEL_API_KEY" in st.secrets:
                key = str(st.secrets["HYPIXEL_API_KEY"]).strip()
        except Exception:
            pass
    return key


# --- PAGE SETUP ---
st.set_page_config(
    page_title="SkyBlock Profile Extractor",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo("assets/logo.png", size="medium")

# --- MINIMALIST AESTHETIC STYLING (ZERO GLOW & COMPACT LAYOUT) ---
st.html("""
<style>
    /* Absolute Zero Glow Invariant */
    *, *::before, *::after {
        box-shadow: none !important;
        text-shadow: none !important;
        filter: none !important;
    }

    /* Base page styling */
    .stApp {
        background-color: #09090b;
        color: #f4f4f5;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Compact Headings */
    h1 {
        font-size: 1.55rem !important;
        font-weight: 600 !important;
        color: #fafafa !important;
        letter-spacing: -0.02em;
        margin: 0 0 0.2rem 0 !important;
    }
    h2 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #fafafa !important;
        letter-spacing: -0.02em;
        margin: 0 0 0.2rem 0 !important;
    }
    h3 {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #fafafa !important;
        margin: 0 0 0.2rem 0 !important;
    }
    h4, h5, h6 {
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        color: #fafafa !important;
        margin: 0 0 0.15rem 0 !important;
    }
    p {
        margin-bottom: 0.3rem !important;
        font-size: 0.88rem !important;
    }

    /* Compact Block Spacing */
    div[data-testid="stVerticalBlock"] {
        gap: 0.55rem !important;
    }
    div[data-testid="stHorizontalBlock"] {
        gap: 0.55rem !important;
    }

    /* Clean Card Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #27272a !important;
        border-radius: 6px !important;
        background-color: #111114 !important;
        padding: 10px 14px !important;
    }

    /* Minimal Native Metrics */
    div[data-testid="stMetric"] {
        padding: 2px 0 !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #38bdf8 !important;
        letter-spacing: -0.02em;
        line-height: 1.2 !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 500 !important;
        color: #a1a1aa !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Restrained Buttons - Clean, Crisp, Flat */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 0.86rem !important;
        border: 1px solid #3f3f46 !important;
        background-color: #18181b !important;
        color: #f4f4f5 !important;
        padding: 4px 14px !important;
        min-height: 36px !important;
        transition: background-color 0.12s ease, border-color 0.12s ease !important;
    }
    .stButton > button:hover {
        border-color: #71717a !important;
        background-color: #27272a !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #2563eb !important;
        border-color: #2563eb !important;
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
        border-color: #1d4ed8 !important;
    }

    /* Clean Modern Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #27272a;
        padding-bottom: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 34px;
        border-radius: 6px;
        padding: 0 14px;
        font-weight: 500;
        font-size: 0.85rem;
        color: #a1a1aa;
        border: 1px solid transparent;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #fafafa !important;
        background: #18181b !important;
        border-color: #3f3f46 !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Compact Checkboxes */
    div[data-testid="stCheckbox"] {
        margin-bottom: 2px !important;
        padding-top: 1px !important;
        padding-bottom: 1px !important;
    }
    div[data-testid="stCheckbox"] label span {
        font-size: 0.82rem !important;
    }

    /* Compact Priority Item */
    .priority-item {
        display: flex;
        align-items: center;
        gap: 10px;
        background-color: #131316;
        border: 1px solid #27272a;
        border-radius: 6px;
        padding: 8px 12px;
        margin-bottom: 6px;
        font-size: 0.86rem;
        color: #e4e4e7;
        line-height: 1.35;
    }
    .priority-badge {
        display: inline-block;
        background-color: #1e293b;
        color: #38bdf8;
        border: 1px solid #334155;
        border-radius: 4px;
        padding: 1px 7px;
        font-size: 0.70rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        white-space: nowrap;
    }
    .priority-text {
        flex: 1;
    }

    /* Clean Inputs */
    input, textarea, select {
        border-radius: 6px !important;
        font-size: 0.88rem !important;
    }

    /* Progress Bar */
    div[data-testid="stProgress"] > div > div > div > div {
        background-color: #2563eb !important;
    }
</style>
""")

# --- STATE INITIALIZATION ---
if "profiles" not in st.session_state:
    st.session_state.profiles = None
if "player_uuid" not in st.session_state:
    st.session_state.player_uuid = None
if "player_username" not in st.session_state:
    st.session_state.player_username = None
if "last_queried_username" not in st.session_state:
    st.session_state.last_queried_username = None
if "extraction_results" not in st.session_state:
    st.session_state.extraction_results = None
if "summary" not in st.session_state:
    st.session_state.summary = None
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "zip_filename" not in st.session_state:
    st.session_state.zip_filename = None
if "public_results" not in st.session_state:
    st.session_state.public_results = None
if "public_zip_buffer" not in st.session_state:
    st.session_state.public_zip_buffer = None
if "public_zip_filename" not in st.session_state:
    st.session_state.public_zip_filename = None
if "public_outcome" not in st.session_state:
    st.session_state.public_outcome = None

# --- SIDEBAR: AUTHENTICATION, GUIDES & POLICIES ---
with st.sidebar:
    st.markdown("### Configuration")

    hosted_mode = is_hosted_environment()
    streamlit_cloud_mode = is_streamlit_cloud()
    allow_storage = can_persist_key_to_disk()
    server_key = resolve_server_api_key()
    key_file = Path("api_key.txt")
    file_key = ""

    if streamlit_cloud_mode or hosted_mode:
        api_key_input = ""
        effective_key = server_key

        if server_key:
            with st.container(border=True):
                st.markdown("**:material/cloud_done: Server Credentials Active**")
                st.caption("Running with pre-configured server credentials. Profile queries are authenticated securely.")
        elif streamlit_cloud_mode:
            with st.container(border=True):
                st.markdown("**:material/cloud: Streamlit Community Cloud**")
                st.caption(
                    "This public instance is hosted on Streamlit Community Cloud. "
                    "Under Hypixel Developer Policies, personal API keys are not collected through web forms on public hosted sites.\n\n"
                    "- **Public Schemas**: You can extract unauthenticated Items, Skills, and Collections schemas under the Public Game Resources tab.\n"
                    "- **Private Player Profiles**: Fork this repository and deploy your own private Streamlit Cloud app (adding your key in App Secrets) or run locally."
                )
        else:
            with st.container(border=True):
                st.markdown("**:material/lock: Hosted Multi-User Mode**")
                st.caption(
                    "Under Hypixel Developer Policies, personal API keys must not be collected through hosted web forms. "
                    "You can extract unauthenticated Public Game Resources (Items, Skills, Collections) in the Public Resources tab, "
                    "or run this tool locally on your own machine to query profiles using a personal API key."
                )
    else:
        if allow_storage and key_file.exists():
            try:
                file_key = key_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        with st.container(border=True):
            st.markdown("**:material/computer: Local Desktop Workspace**")
            st.caption("Running locally on your machine. API keys remain strictly in memory on your device.")

            api_key_input = st.text_input(
                "Hypixel API Key",
                value=file_key,
                type="password",
                help="Personal API Key from developer.hypixel.net. Stored in memory on your local machine.",
            )

            effective_key = api_key_input.strip() or server_key

            if allow_storage:
                save_key = st.checkbox("Persist key locally to api_key.txt", value=bool(file_key))
                if save_key and api_key_input.strip() and api_key_input.strip() != file_key:
                    try:
                        key_file.write_text(api_key_input.strip(), encoding="utf-8")
                        st.toast("API key saved locally.")
                    except Exception as e:
                        st.error(f"Failed to persist key: {e}")
                elif not save_key and key_file.exists():
                    try:
                        key_file.unlink()
                    except Exception:
                        pass

    # HOW TO GET AN API KEY
    with st.expander("**:material/help_outline: How to Get an API Key**", expanded=False):
        st.markdown("""
        **Step-by-step Guide:**
        1. Open the [Hypixel Developer Portal](https://developer.hypixel.net/).
        2. Log in using your Microsoft account linked to your Minecraft profile.
        3. Click **Create API Key** or register a **Personal Application**.
        4. Copy your generated `API-Key` UUID token.
        5. Paste it into the **Hypixel API Key** field above (or configure it in `secrets.toml` if deploying to Streamlit Cloud).

        **Key Details:**
        - Personal API keys are free and provide standard rate limits (300 requests/minute).
        - Keep your API key private; never share it with anyone.
        """)
        st.link_button(
            "Open Hypixel Developer Portal",
            "https://developer.hypixel.net/",
            icon=":material/open_in_new:",
            width="stretch",
        )

    # STREAMLIT CLOUD DEPLOYMENT GUIDE
    with st.expander("**:material/rocket_launch: Deploy on Streamlit Cloud**", expanded=False):
        st.markdown("""
        You can host your own private, 24/7 profile extractor on Streamlit Community Cloud for personal use:

        1. **Fork** this repository to your personal GitHub account.
        2. Navigate to [share.streamlit.io](https://share.streamlit.io/) and select **New app**.
        3. Choose your repository fork, branch, and set `app.py` as the main file path.
        4. In **Advanced settings > Secrets**, define:
        ```toml
        HYPIXEL_API_KEY = "your-hypixel-api-key-here"
        ```
        5. Click **Deploy**. Your private cloud instance will authenticate requests securely via server-side secrets!
        """)

    # API SECURITY & POLICY
    with st.expander("**:material/verified_user: Hypixel Policy Compliance**", expanded=False):
        st.markdown("""
        - Requests authenticate via HTTP headers (`API-Key`).
        - Data is queried on-demand upon direct user click.
        - Strict rate-limit tracking with exponential backoff recovery.
        - Zero background polling or continuous player surveillance.
        - Strictly conforms to [Hypixel Developer Policies](https://developer.hypixel.net/policies/).
        """)

    # PRIVACY POLICY
    with st.expander("**:material/privacy_tip: Privacy Policy**", expanded=False):
        st.markdown("""
        **Zero External Data Storage:**
        - **No Database**: This application does not store, transmit, or record player statistics or API keys to external servers or databases.
        - **In-Memory Lifecycle**: Profile, inventory, and progression calculations occur purely within your transient browser session.
        - **Local Archives**: Exported JSON packages and ZIP archives are generated directly in browser memory for personal offline analysis.
        - **Key Confidentiality**: On desktop, keys are held in memory (or written to local `api_key.txt` solely upon explicit opt-in). On hosted deployments, visitor key inputs are entirely disabled to prevent credential exposure.
        - **Zero Tracking**: Contains no telemetry beacons, tracking cookies, or advertising scripts.
        """)

    # TERMS AND CONDITIONS
    with st.expander("**:material/gavel: Terms and Conditions**", expanded=False):
        st.markdown("""
        **Terms of Service:**
        - **Personal Use**: Intended solely for personal SkyBlock progression review, account backup, and offline data analysis.
        - **Acceptable Use**: Users agree not to misuse or flood Hypixel API services. Automated scraping or unauthorized mass querying is prohibited.
        - **Non-Affiliation**: This independent open-source project is not affiliated with, endorsed by, or sponsored by Hypixel Inc., Mojang Synergies AB, or Microsoft Corporation.
        - **Software License**: Distributed under the MIT License. Provided "as is" without warranty of any kind, express or implied.
        """)

    st.divider()
    st.caption(f"SkyBlock Profile Extractor v{APP_VERSION}")
    st.caption("Not affiliated with or endorsed by Hypixel Inc.")

# --- MAIN INTERFACE ---
c_title, c_badge = st.columns([4, 1], vertical_alignment="center")
with c_title:
    st.title("SkyBlock Profile Extractor")
    st.markdown("Export raw Hypixel SkyBlock profile data and deterministic progression analytics for personal analysis.")
with c_badge:
    if streamlit_cloud_mode:
        st.badge("Streamlit Cloud", icon=":material/cloud:", color="blue")
    elif hosted_mode:
        st.badge("Hosted Server", icon=":material/dns:", color="blue")
    else:
        st.badge("Local Desktop", icon=":material/computer:", color="green")

tab_player, tab_public = st.tabs([
    ":material/person: Player Profile Backup",
    ":material/database: Public Game Resources",
])

with tab_player:
    if (streamlit_cloud_mode or hosted_mode) and not effective_key:
        st.info(
            "Streamlit Community Cloud Deployment: In compliance with Hypixel Developer Policies, personal API keys are not collected "
            "through web forms on public hosted sites. You can extract official public datasets (Items, Skills, Collections) under the "
            "Public Game Resources tab, or deploy your own private copy to Streamlit Cloud / run locally for private player profile exports.",
            icon=":material/cloud:",
        )

    # STEP 1: USERNAME INPUT
    with st.form("player_lookup", border=True):
        st.markdown("**:material/person_search: Player lookup**")
        c_input, c_btn = st.columns([4, 1], vertical_alignment="bottom")
        with c_input:
            input_username = st.text_input(
                "Minecraft username",
                placeholder="e.g. Technoblade",
                label_visibility="visible",
            )
        with c_btn:
            find_btn = st.form_submit_button("Find profiles", icon=":material/search:", width="stretch", type="primary")

    # Keep the current results until a different player search is submitted.
    if find_btn and input_username.strip() != st.session_state.last_queried_username:
        st.session_state.profiles = None
        st.session_state.extraction_results = None
        st.session_state.summary = None
        st.session_state.zip_buffer = None

    if find_btn:
        if not input_username.strip():
            st.warning("Please enter a Minecraft username.", icon=":material/warning:")
        elif not effective_key:
            st.warning("Please provide a Hypixel API key in the sidebar. On hosted deployments, use the Public Game Resources tab or run locally.", icon=":material/warning:")
        else:
            st.session_state.last_queried_username = input_username.strip()
            client = HypixelAPIClient(api_key=effective_key)
            
            with st.spinner("Resolving player and fetching profiles..."):
                try:
                    dashed_uuid, raw_uuid = client.get_player_uuid(input_username.strip())
                    st.session_state.player_uuid = dashed_uuid
                    st.session_state.player_username = input_username.strip()

                    raw_profiles = client.get_skyblock_profiles(dashed_uuid)
                    if not raw_profiles:
                        st.error("No SkyBlock profiles found for this account.", icon=":material/error:")
                        st.session_state.profiles = None
                    else:
                        normalized = normalize_profiles(raw_profiles, dashed_uuid)
                        st.session_state.profiles = normalized
                        st.session_state.extraction_results = None
                        st.session_state.summary = None
                        st.session_state.zip_buffer = None
                        st.success(f"Found {len(normalized)} profile(s) for {input_username.strip()}.", icon=":material/check_circle:")
                except PlayerNotFoundError as e:
                    st.error(f"Player resolution error: {e}", icon=":material/error:")
                    st.session_state.profiles = None
                except AuthenticationError as e:
                    st.error(f"Authentication error: {e}", icon=":material/error:")
                    st.session_state.profiles = None
                except RateLimitExceededError as e:
                    st.error(f"Rate limit exceeded: {e}", icon=":material/error:")
                    st.session_state.profiles = None
                except SkyBlockExtractorError as e:
                    st.error(f"API Error: {e}", icon=":material/error:")
                    st.session_state.profiles = None

    # STEP 2 & 3: PROFILE SELECTION & CATEGORY CONFIGURATION
    if st.session_state.profiles:
        st.markdown("**:material/tune: Profile & Extraction Scope**")

        col_profile, col_categories = st.columns(2)

        with col_profile:
            with st.container(border=True):
                st.markdown("##### Target Profile")
                st.caption("Select the SkyBlock profile to analyze and export.")

                profile_choices = {}
                for p in st.session_state.profiles:
                    last_save_fmt = (
                        datetime.fromtimestamp(p["last_save"] / 1000).strftime("%Y-%m-%d %H:%M")
                        if p["last_save"] > 0
                        else "Never"
                    )
                    mode_tag = f"[{p['game_mode'].upper()}]" if p["game_mode"] != "normal" else ""
                    label = f"{p['name']} {mode_tag} - Last Save: {last_save_fmt}".strip()
                    profile_choices[label] = p

                selected_label = st.radio(
                    "Target Profile",
                    options=list(profile_choices.keys()),
                    index=0,
                    label_visibility="collapsed",
                )
                target_profile = profile_choices[selected_label]

                # Profile metadata summary
                last_save_val = (
                    datetime.fromtimestamp(target_profile["last_save"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    if target_profile["last_save"] > 0
                    else "Never recorded"
                )
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    st.caption(f"**Mode:** {target_profile['game_mode'].capitalize()}")
                    st.caption(f"**Profile ID:** `{target_profile['profile_id'][:8]}...`")
                with c_p2:
                    st.caption(f"**Last Save:** {last_save_val}")
                    st.caption(f"**Profile Name:** {target_profile['name']}")

        with col_categories:
            with st.container(border=True):
                st.markdown("##### Extraction Datasets")
                st.caption("Choose which categories to query.")
                c_cat1, c_cat2 = st.columns(2)
                with c_cat1:
                    chk_profile = st.checkbox("Complete Profile", value=True, disabled=True, help="Inventories, skills, slayers, dungeons")
                    chk_player = st.checkbox("Player Stats", value=True, help="Overall player stats & minigame achievements")
                    chk_garden = st.checkbox("Garden & Farming", value=True, help="Plots, crops, milestones, visitors")
                    chk_museum = st.checkbox("Museum Collection", value=True, help="Donated weapons, armor, appraisals")
                    chk_guild = st.checkbox("Guild Membership", value=True, help="Guild level, members, exp")
                    chk_bazaar = st.checkbox("Bazaar Snapshot", value=True, help="Live buy/sell market snapshot")
                with c_cat2:
                    chk_auction = st.checkbox("Profile Auctions", value=True, help="Active & ended player auctions")
                    chk_news = st.checkbox("In-Game News", value=False, help="Recent SkyBlock maintenance/update news")
                    chk_firesales = st.checkbox("Fire Sales", value=False, help="Active cosmetic fire sales")
                    chk_items = st.checkbox("Items Schema", value=True, help="Official item definitions (Public)")
                    chk_skills_res = st.checkbox("Skills Schema", value=False, help="Official skill formulas (Public)")
                    chk_colls_res = st.checkbox("Collections Schema", value=False, help="Official collection milestones (Public)")

        selected_categories = ["profile"]
        if chk_player: selected_categories.append("player")
        if chk_garden: selected_categories.append("garden")
        if chk_museum: selected_categories.append("museum")
        if chk_guild: selected_categories.append("guild")
        if chk_bazaar: selected_categories.append("bazaar")
        if chk_auction: selected_categories.append("auction")
        if chk_news: selected_categories.append("news")
        if chk_firesales: selected_categories.append("firesales")
        if chk_items: selected_categories.append("items")
        if chk_skills_res: selected_categories.append("skills_resource")
        if chk_colls_res: selected_categories.append("collections_resource")

        # STEP 4: EXTRACTION TRIGGER
        if st.button("Start Extraction", icon=":material/download:", type="primary", width="stretch"):
            client = HypixelAPIClient(api_key=effective_key)
            progress_bar = st.progress(0, text="Initializing extraction pipeline...")
            status_text = st.empty()

            def update_progress(step: int, total: int, category: str, status: str):
                pct = int((step / total) * 100)
                progress_bar.progress(pct, text=f"Fetching category: {category} ({step}/{total})")

            extractor = ProfileExtractor(client=client, progress_callback=update_progress)

            with st.spinner("Extracting datasets from Hypixel API v2..."):
                results = extractor.extract(
                    player_uuid=st.session_state.player_uuid,
                    profile=target_profile,
                    categories=selected_categories,
                )

                outcome = classify_extraction_outcome(results)
                st.session_state.extraction_results = results
                st.session_state.extraction_outcome = outcome

                if outcome["status"] == "complete_failure":
                    st.session_state.summary = None
                    st.session_state.zip_buffer = None
                    st.session_state.zip_filename = None
                    progress_bar.progress(100, text="Extraction failed for all requested endpoints.")
                    st.error("Extraction failed: None of the requested endpoints succeeded. Please verify API credentials and player privacy settings.", icon=":material/error:")
                else:
                    # Prioritize freshly extracted profile data if available
                    fresh_profile_data = None
                    if "profile" in results and results["profile"].status == "success" and results["profile"].data:
                        fresh_profile_data = results["profile"].data

                    profile_payload_for_analysis = fresh_profile_data or target_profile.get("data", target_profile)

                    # Analyze progression
                    analyzer = ProfileAnalyzer()
                    auxiliary = {cat: res.data for cat, res in results.items() if res.status == "success" and res.data}
                    summary = analyzer.analyze(
                        player_uuid=st.session_state.player_uuid,
                        profile_data=profile_payload_for_analysis,
                        auxiliary_data=auxiliary,
                    )

                    # Build in-memory bundle
                    exporter = ProfileExporter(
                        username=st.session_state.player_username,
                        player_uuid=st.session_state.player_uuid,
                        profile_name=target_profile["name"],
                        profile_id=target_profile["profile_id"],
                        results=results,
                        summary=summary,
                    )

                    zip_buffer = exporter.build_zip_in_memory()
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_name = f"SkyBlock_{st.session_state.player_username}_{target_profile['name']}_{ts}.zip"

                    st.session_state.summary = summary
                    st.session_state.zip_buffer = zip_buffer
                    st.session_state.zip_filename = zip_name

                    if outcome["status"] == "complete_success":
                        progress_bar.progress(100, text=f"Extraction completed: All {outcome['total_count']} datasets acquired.")
                        st.success(f"All {outcome['total_count']} datasets successfully extracted.", icon=":material/check_circle:")
                    else:
                        progress_bar.progress(100, text=f"Partial extraction completed: {outcome['success_count']} of {outcome['total_count']} datasets acquired.")
                        st.warning(f"Partial extraction: {outcome['success_count']} of {outcome['total_count']} datasets acquired. Some endpoints failed.", icon=":material/warning:")

    # STEP 5: RESULTS & DOWNLOADS
    if st.session_state.extraction_results:
        st.markdown("**:material/analytics: Extraction Summary & Analytics**")

        results = st.session_state.extraction_results
        outcome = st.session_state.get("extraction_outcome", classify_extraction_outcome(results))
        summary = st.session_state.summary

        if outcome["status"] == "complete_failure":
            st.error("No datasets could be extracted. Review endpoint diagnostics below.", icon=":material/error:")
            tab_endpoints, = st.tabs([":material/network_check: Endpoint Status & Diagnostics"])
            with tab_endpoints:
                status_rows = []
                for cat, r in results.items():
                    status_rows.append({
                        "Category": r.description,
                        "Filename": r.filename,
                        "Status": r.status.upper(),
                        "Details": r.error_message or "Failed to extract",
                    })
                st.table(status_rows)
        elif summary:
            # Highlight metrics with native bordered containers
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric(
                    label="Skill Average",
                    value=summary.get("skill_average") or "N/A",
                    border=True,
                    height="stretch",
                )
            with m2:
                dungeons = summary.get("dungeons", {})
                cata_val = dungeons.get("catacombs_level") if (dungeons.get("available") and dungeons.get("catacombs_level") is not None) else "N/A"
                st.metric(
                    label="Catacombs Level",
                    value=cata_val,
                    border=True,
                    height="stretch",
                )
            with m3:
                slayers = summary.get("slayer", {})
                zombie_lvl = slayers.get("zombie", {}).get("level") if slayers.get("available") else None
                zombie_val = f"Lvl {zombie_lvl}" if zombie_lvl is not None else "N/A"
                st.metric(
                    label="Zombie Slayer",
                    value=zombie_val,
                    border=True,
                    height="stretch",
                )
            with m4:
                st.metric(
                    label="Datasets Acquired",
                    value=f"{outcome['success_count']} / {outcome['total_count']}",
                    border=True,
                    height="stretch",
                )

            # Downloads section
            if st.session_state.zip_buffer:
                st.download_button(
                    label=f"Download Complete Archive ({st.session_state.zip_filename})",
                    icon=":material/download:",
                    data=st.session_state.zip_buffer.getvalue(),
                    file_name=st.session_state.zip_filename,
                    mime="application/zip",
                    type="primary",
                    width="stretch",
                )

            # Progression Priorities Tab
            tab_priorities, tab_endpoints, tab_files = st.tabs([
                ":material/checklist: Progression Priorities",
                ":material/network_check: Endpoint Status",
                ":material/code: File Previews",
            ])

            with tab_priorities:
                st.markdown("**:material/checklist: Rule-Based Progression Recommendations**")
                priorities = summary.get("progression_priorities", [])
                if priorities:
                    for idx, item in enumerate(priorities, 1):
                        st.markdown(
                            f"""<div class="priority-item">
                                <span class="priority-badge">Priority {idx}</span>
                                <span class="priority-text">{item}</span>
                            </div>""",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No specific progression recommendations generated for this profile.", icon=":material/info:")

                st.caption("Note: Recommendations are derived using deterministic game logic. Progression data depends on enabled in-game API settings.")

            with tab_endpoints:
                st.markdown("**:material/network_check: Endpoint Extraction Status**")
                status_rows = []
                for cat, r in results.items():
                    status_rows.append({
                        "Category": r.description,
                        "Filename": r.filename,
                        "Status": r.status.upper(),
                        "Details": r.error_message or "Extracted cleanly",
                    })
                st.table(status_rows)

            with tab_files:
                preview_category = st.selectbox(
                    "Select file to inspect:",
                    options=[k for k, v in results.items() if v.status == "success"],
                    format_func=lambda k: f"{results[k].filename} ({results[k].description})",
                )
                if preview_category and results[preview_category].data is not None:
                    st.json(results[preview_category].data, expanded=False)

with tab_public:
    with st.container(border=True):
        st.markdown("**:material/public: Public Game Resources (Keyless)**")
        st.caption(
            "Extract official Hypixel SkyBlock item schemas, skill definitions, and collection unlock milestones. "
            "These public endpoints require no API key, no Minecraft username, and no player authentication."
        )

        c_pub1, c_pub2, c_pub3 = st.columns(3)
        with c_pub1:
            chk_pub_items = st.checkbox(
                "Items Schema",
                value=True,
                help="Official SkyBlock item definitions, weapon/armor stats, and rarity levels.",
            )
        with c_pub2:
            chk_pub_skills = st.checkbox(
                "Skills Schema",
                value=True,
                help="Official skill types, level caps, and leveling formulas.",
            )
        with c_pub3:
            chk_pub_collections = st.checkbox(
                "Collections Schema",
                value=True,
                help="Official collection categories, items, and unlock milestones.",
            )

        selected_pub_categories = []
        if chk_pub_items:
            selected_pub_categories.append("items")
        if chk_pub_skills:
            selected_pub_categories.append("skills_resource")
        if chk_pub_collections:
            selected_pub_categories.append("collections_resource")

        pub_trigger = st.button("Extract Public Resources", icon=":material/cloud_download:", type="primary", width="stretch")

    if pub_trigger:
        if not selected_pub_categories:
            st.warning("Please select at least one public resource to extract.", icon=":material/warning:")
        else:
            pub_client = HypixelAPIClient(api_key=None)
            pub_progress = st.progress(0, text="Fetching public resources...")

            def update_pub_progress(step: int, total: int, category: str, status: str):
                pct = int((step / total) * 100)
                pub_progress.progress(pct, text=f"Fetching {category} ({step}/{total})")

            pub_extractor = ProfileExtractor(client=pub_client, progress_callback=update_pub_progress)
            with st.spinner("Querying Hypixel public resource endpoints..."):
                pub_results = pub_extractor.extract_public_resources(selected_pub_categories)
                pub_outcome = classify_extraction_outcome(pub_results)
                st.session_state.public_results = pub_results
                st.session_state.public_outcome = pub_outcome

                if pub_outcome["status"] == "complete_failure":
                    st.session_state.public_zip_buffer = None
                    st.session_state.public_zip_filename = None
                    pub_progress.progress(100, text="Public resource extraction failed for all requested endpoints.")
                    st.error("Extraction failed: None of the requested public resource endpoints responded successfully. Please verify your network connection and Hypixel API status.", icon=":material/error:")
                else:
                    pub_exporter = PublicResourceExporter(results=pub_results)
                    pub_zip_buffer = pub_exporter.build_zip_in_memory()
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pub_zip_name = f"SkyBlock_Public_Resources_{ts}.zip"

                    st.session_state.public_zip_buffer = pub_zip_buffer
                    st.session_state.public_zip_filename = pub_zip_name

                    if pub_outcome["status"] == "complete_success":
                        pub_progress.progress(100, text=f"All {pub_outcome['total_count']} public resources extracted successfully.")
                        st.success(f"All {pub_outcome['total_count']} public resource schemas successfully extracted.", icon=":material/check_circle:")
                    else:
                        pub_progress.progress(100, text=f"Partial extraction completed: {pub_outcome['success_count']} of {pub_outcome['total_count']} public resources acquired.")
                        st.warning(f"Partial extraction: {pub_outcome['success_count']} of {pub_outcome['total_count']} public resources acquired. Some endpoints failed.", icon=":material/warning:")

    if st.session_state.public_results:
        st.markdown("**:material/inventory_2: Extracted Public Resources**")

        pub_res = st.session_state.public_results
        pub_outcome = st.session_state.get("public_outcome", classify_extraction_outcome(pub_res))

        if pub_outcome["status"] == "complete_failure":
            st.error("No public resource datasets could be extracted. Review diagnostics below.", icon=":material/error:")
            pub_rows = []
            for cat, r in pub_res.items():
                pub_rows.append({
                    "Schema": r.description,
                    "Filename": r.filename,
                    "Status": r.status.upper(),
                    "Details": r.error_message or "Failed to extract",
                })
            st.table(pub_rows)
        else:
            if st.session_state.public_zip_buffer:
                st.download_button(
                    label=f"Download Public Resources Archive ({st.session_state.public_zip_filename})",
                    icon=":material/download:",
                    data=st.session_state.public_zip_buffer.getvalue(),
                    file_name=st.session_state.public_zip_filename,
                    mime="application/zip",
                    type="primary",
                    width="stretch",
                )

            tab_pub_status, tab_pub_preview = st.tabs([
                ":material/network_check: Extraction Status",
                ":material/code: Schema Inspector",
            ])
            with tab_pub_status:
                pub_rows = []
                for cat, r in pub_res.items():
                    pub_rows.append({
                        "Schema": r.description,
                        "Filename": r.filename,
                        "Status": r.status.upper(),
                        "Details": r.error_message or "Extracted cleanly",
                    })
                st.table(pub_rows)

            with tab_pub_preview:
                preview_cat = st.selectbox(
                    "Select schema to preview:",
                    options=[k for k, v in pub_res.items() if v.status == "success"],
                    format_func=lambda k: f"{pub_res[k].filename} ({pub_res[k].description})",
                )
                if preview_cat and pub_res[preview_cat].data is not None:
                    st.json(pub_res[preview_cat].data, expanded=False)
