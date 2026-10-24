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

# --- PAGE SETUP ---
st.set_page_config(
    page_title="SkyBlock Profile Extractor",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.logo("assets/logo.png", size="medium")

# --- MINIMALIST AESTHETIC STYLING (ZERO GLOW) ---
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

    /* Clean Headings */
    h1, h2, h3, h4, h5, h6 {
        color: #fafafa !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* Clean Card Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border-color: #27272a !important;
        border-radius: 8px !important;
        background-color: #111114 !important;
    }

    /* Minimal Native Metrics */
    div[data-testid="stMetric"] {
        padding: 4px 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        font-weight: 600 !important;
        color: #38bdf8 !important;
        letter-spacing: -0.02em;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        color: #a1a1aa !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Restrained Buttons - Clean, Crisp, Flat */
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        border: 1px solid #3f3f46 !important;
        background-color: #18181b !important;
        color: #f4f4f5 !important;
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
        gap: 6px;
        border-bottom: 1px solid #27272a;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 6px;
        padding: 0 16px;
        font-weight: 500;
        font-size: 0.88rem;
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

    /* Clean Inputs */
    input, textarea, select {
        border-radius: 6px !important;
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

# --- SIDEBAR: AUTHENTICATION & CONFIG ---
with st.sidebar:
    st.markdown("### Configuration")

    hosted_mode = is_hosted_environment()
    allow_storage = can_persist_key_to_disk()
    env_key = os.environ.get("HYPIXEL_API_KEY", "").strip()
    key_file = Path("api_key.txt")
    file_key = ""

    if hosted_mode:
        api_key_input = ""
        effective_key = env_key
        if env_key:
            st.success("Server API key active", icon=":material/check_circle:")
            st.caption("Using server-configured Hypixel API credentials.")
        else:
            with st.container(border=True):
                st.markdown("**:material/lock: Hosted Multi-User Mode**")
                st.caption(
                    "Under Hypixel Developer Policies, personal API keys must not be collected through hosted web forms. "
                    "You can freely extract unauthenticated Public Game Resources (Items, Skills, Collections) in the Public Resources tab, "
                    "or run this tool locally on your own machine to query profiles using a personal API key."
                )
    else:
        if allow_storage and key_file.exists():
            try:
                file_key = key_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        with st.container(border=True):
            st.markdown("**:material/key: Personal API Key**")
            api_key_input = st.text_input(
                "Hypixel API Key",
                value=file_key,
                type="password",
                help="Personal API Key from developer.hypixel.net. Stored in memory on your local machine.",
            )

            effective_key = api_key_input.strip() or env_key

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

    st.space("small")
    with st.expander("API Security & Policy", expanded=False):
        st.markdown("""
        **:material/verified_user: Compliance Checklist**
        - Requests use HTTP header auth (`API-Key`).
        - Data is fetched on demand per user action.
        - No continuous polling or player monitoring.
        - Free, open-source personal utility.
        """)
        st.caption("[Hypixel Developer Policies](https://developer.hypixel.net/policies/)")

    st.divider()
    st.caption(f"SkyBlock Profile Extractor v{APP_VERSION}")
    st.caption("Not affiliated with or endorsed by Hypixel Inc.")

# --- MAIN INTERFACE ---
c_title, c_badge = st.columns([4, 1], vertical_alignment="center")
with c_title:
    st.title("SkyBlock Profile Extractor")
    st.markdown("Export raw Hypixel SkyBlock profile data and deterministic progression analytics for personal analysis.")
with c_badge:
    if hosted_mode:
        st.badge("Hosted Mode", icon=":material/cloud:", color="blue")
    else:
        st.badge("Local Mode", icon=":material/computer:", color="green")

tab_player, tab_public = st.tabs([
    ":material/person: Player Profile Backup",
    ":material/database: Public Game Resources",
])

with tab_player:
    if hosted_mode and not effective_key:
        st.info(
            "Hosted Multi-User Deployment: In compliance with Hypixel Developer Policies, personal API keys are not collected "
            "through web forms on hosted sites. To back up your private player profiles, please run this application locally on your computer. "
            "You can extract official unauthenticated public datasets without an API key under the Public Game Resources tab.",
            icon=":material/info:",
        )

    # STEP 1: USERNAME INPUT
    with st.container(border=True):
        st.markdown("**:material/person_search: Player Lookup**")
        c_input, c_btn = st.columns([4, 1], vertical_alignment="bottom")
        with c_input:
            input_username = st.text_input(
                "Minecraft Username",
                placeholder="e.g. Technoblade",
                label_visibility="visible",
            )
        with c_btn:
            find_btn = st.button("Find Profiles", icon=":material/search:", width="stretch", type="primary")

    # Reset downstream state if username changes
    if input_username != st.session_state.last_queried_username:
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
        st.space("small")
        st.markdown("**:material/tune: Profile & Extraction Scope**")

        col_profile, col_categories = st.columns(2)

        with col_profile:
            with st.container(border=True, height="stretch"):
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

        with col_categories:
            with st.container(border=True, height="stretch"):
                st.markdown("##### Datasets")
                st.caption("Choose which categories to query.")
                chk_profile = st.checkbox("Complete Profile (Inventories, Skills, Slayers, Dungeons)", value=True, disabled=True)
                chk_player = st.checkbox("Global Player & Minigame Stats", value=True)
                chk_garden = st.checkbox("Garden & Farming Data", value=True)
                chk_museum = st.checkbox("Museum Collection & Appraisals", value=True)
                chk_guild = st.checkbox("Guild Membership & Experience", value=True)
                chk_bazaar = st.checkbox("Bazaar Market Snapshot", value=True)
                chk_auction = st.checkbox("Active Profile Auctions", value=True)
                chk_news = st.checkbox("SkyBlock In-game News", value=False)
                chk_firesales = st.checkbox("Active Fire Sales", value=False)
                chk_items = st.checkbox("Items Schema (Public Resource)", value=True)
                chk_skills_res = st.checkbox("Skills Schema (Public Resource)", value=False)
                chk_colls_res = st.checkbox("Collections Schema (Public Resource)", value=False)

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
        st.space("small")
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
        st.space("medium")
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
                st.space("small")
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
                st.markdown("**Rule-Based Next Steps:**")
                priorities = summary.get("progression_priorities", [])
                for item in priorities:
                    st.info(item, icon=":material/arrow_forward:")

                st.caption("Note: Recommendations are derived using deterministic game logic. Progression data depends on enabled in-game API settings.")

            with tab_endpoints:
                st.markdown("**Endpoint Extraction Status:**")
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

        st.space("small")
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
        st.space("medium")
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
                st.space("small")
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
