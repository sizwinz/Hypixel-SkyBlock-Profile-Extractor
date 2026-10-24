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
    page_icon='assets/logo.png',
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- REFINED PROFESSIONAL STYLING ---
st.markdown("""
<style>
    /* Executive typography & restrained contrast */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Headers */
    h1, h2, h3, h4 {
        color: #f0f6fc;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Clean Cards */
    .metric-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .metric-val {
        font-size: 1.6rem;
        font-weight: 700;
        color: #58a6ff;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Badge Pills */
    .badge-ok {
        background-color: rgba(46, 160, 67, 0.15);
        color: #3fb950;
        border: 1px solid rgba(46, 160, 67, 0.4);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-fail {
        background-color: rgba(248, 81, 73, 0.15);
        color: #f85149;
        border: 1px solid rgba(248, 81, 73, 0.4);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .badge-mode {
        background-color: rgba(88, 166, 255, 0.15);
        color: #58a6ff;
        border: 1px solid rgba(88, 166, 255, 0.3);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Subdued Buttons */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
</style>
""", unsafe_allow_html=True)


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


# --- SIDEBAR: AUTHENTICATION & CONFIG ---
with st.sidebar:
    st.title("Configuration")
    
    # Resolve initial default key without exposing server environment key
    hosted_mode = is_hosted_environment()
    allow_storage = can_persist_key_to_disk()
    env_key = os.environ.get("HYPIXEL_API_KEY", "").strip()
    key_file = Path("api_key.txt")
    file_key = ""

    if hosted_mode:
        # In hosted deployments, visitors must never be prompted or permitted to enter personal API keys
        api_key_input = ""
        effective_key = env_key
        if env_key:
            st.success("Server API Key Active")
            st.caption("Using server-configured Hypixel API credentials.")
        else:
            st.info("Hosted Multi-User Deployment")
            st.caption(
                "Under Hypixel Developer Policies, personal API keys must not be collected through hosted web forms. "
                "You can freely extract unauthenticated Public Game Resources (Items, Skills, Collections) in the Public Resources tab, "
                "or run this tool locally on your own machine to query profiles using a personal API key."
            )
    else:
        # Desktop local deployment: user can provide their own personal API key safely
        if allow_storage and key_file.exists():
            try:
                file_key = key_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

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

    st.markdown("---")
    with st.expander("API Security & Policy", expanded=False):
        st.markdown("""
        **Compliance Checklist:**
        - Requests use HTTP header auth (`API-Key`).
        - Data is fetched on-demand per user click.
        - No continuous polling or player monitoring.
        - Free, open-source personal utility.
        """)
        st.caption("[Hypixel Developer Policies](https://developer.hypixel.net/policies/)")

    st.markdown("---")
    st.caption(f"SkyBlock Profile Extractor v{APP_VERSION}")
    st.caption("Not affiliated with or endorsed by Hypixel Inc.")


# --- MAIN INTERFACE ---
st.title("SkyBlock Profile Extractor")
st.markdown("Export raw Hypixel SkyBlock profile data and deterministic progression analytics for personal analysis.")

tab_player, tab_public = st.tabs([
    "Player Profile Backup",
    "Public Game Resources",
])

with tab_player:
    if hosted_mode and not effective_key:
        st.info(
            "Hosted Multi-User Deployment: In compliance with Hypixel Developer Policies, personal API keys are not collected "
            "through web forms on hosted sites. To back up your private player profiles, please run this application locally on your computer. "
            "You can extract official unauthenticated public datasets without an API key under the Public Game Resources tab."
        )

    # STEP 1: USERNAME INPUT
    c_input, c_btn = st.columns([3, 1])
    with c_input:
        input_username = st.text_input(
            "Minecraft Username",
            placeholder="e.g. Technoblade",
            label_visibility="collapsed",
        )
    with c_btn:
        find_btn = st.button("Find Profiles", use_container_width=True, type="primary")

    # Reset downstream state if username changes
    if input_username != st.session_state.last_queried_username:
        st.session_state.profiles = None
        st.session_state.extraction_results = None
        st.session_state.summary = None
        st.session_state.zip_buffer = None

    if find_btn:
        if not input_username.strip():
            st.warning("Please enter a Minecraft username.")
        elif not effective_key:
            st.warning("Please provide a Hypixel API key in the sidebar. On hosted deployments, use the Public Game Resources tab or run locally.")
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
                        st.error("No SkyBlock profiles found for this account.")
                        st.session_state.profiles = None
                    else:
                        normalized = normalize_profiles(raw_profiles, dashed_uuid)
                        st.session_state.profiles = normalized
                        st.session_state.extraction_results = None
                        st.session_state.summary = None
                        st.session_state.zip_buffer = None
                        st.success(f"Found {len(normalized)} profile(s) for **{input_username.strip()}**.")
                except PlayerNotFoundError as e:
                    st.error(f"Player resolution error: {e}")
                    st.session_state.profiles = None
                except AuthenticationError as e:
                    st.error(f"Authentication error: {e}")
                    st.session_state.profiles = None
                except RateLimitExceededError as e:
                    st.error(f"Rate limit exceeded: {e}")
                    st.session_state.profiles = None
                except SkyBlockExtractorError as e:
                    st.error(f"API Error: {e}")
                    st.session_state.profiles = None


    # STEP 2 & 3: PROFILE SELECTION & CATEGORY CONFIGURATION
    if st.session_state.profiles:
        st.divider()
        st.subheader("Select Profile & Categories")

        col_profile, col_categories = st.columns([1, 1])

        with col_profile:
            profile_choices = {}
            for p in st.session_state.profiles:
                last_save_fmt = (
                    datetime.fromtimestamp(p["last_save"] / 1000).strftime("%Y-%m-%d %H:%M")
                    if p["last_save"] > 0
                    else "Never"
                )
                mode_tag = f"[{p['game_mode'].upper()}]" if p["game_mode"] != "normal" else ""
                label = f"{p['name']} {mode_tag} - Last Save: {last_save_fmt}"
                profile_choices[label] = p

            selected_label = st.radio(
                "Target Profile:",
                options=list(profile_choices.keys()),
                index=0,
            )
            target_profile = profile_choices[selected_label]

        with col_categories:
            st.markdown("**Extraction Categories:**")
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
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Start Extraction", type="primary", use_container_width=True):
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
                    st.error("Extraction failed: None of the requested endpoints succeeded. Please verify API credentials and player privacy settings.")
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
                        st.success(f"All {outcome['total_count']} datasets successfully extracted.")
                    else:
                        progress_bar.progress(100, text=f"Partial extraction completed: {outcome['success_count']} of {outcome['total_count']} datasets acquired.")
                        st.warning(f"Partial extraction: {outcome['success_count']} of {outcome['total_count']} datasets acquired. Some endpoints failed.")


    # STEP 5: RESULTS & DOWNLOADS
    if st.session_state.extraction_results:
        st.divider()
        st.subheader("Extraction Summary & Analytics")

        results = st.session_state.extraction_results
        outcome = st.session_state.get("extraction_outcome", classify_extraction_outcome(results))
        summary = st.session_state.summary

        if outcome["status"] == "complete_failure":
            st.error("No datasets could be extracted. Review endpoint diagnostics below.")
            tab_endpoints, = st.tabs(["Endpoint Status & Diagnostics"])
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
            # Highlight metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Skill Average</div>
                    <div class="metric-val">{summary.get('skill_average') or 'N/A'}</div>
                </div>
                """, unsafe_allow_html=True)
            with m2:
                dungeons = summary.get("dungeons", {})
                cata_val = dungeons.get('catacombs_level') if (dungeons.get('available') and dungeons.get('catacombs_level') is not None) else 'N/A'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Catacombs Level</div>
                    <div class="metric-val">{cata_val}</div>
                </div>
                """, unsafe_allow_html=True)
            with m3:
                slayers = summary.get("slayer", {})
                zombie_lvl = slayers.get("zombie", {}).get("level") if slayers.get("available") else None
                zombie_val = f"Lvl {zombie_lvl}" if zombie_lvl is not None else 'N/A'
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Zombie Slayer</div>
                    <div class="metric-val">{zombie_val}</div>
                </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Datasets Acquired</div>
                    <div class="metric-val">{outcome['success_count']}/{outcome['total_count']}</div>
                </div>
                """, unsafe_allow_html=True)

            # Downloads section
            if st.session_state.zip_buffer:
                st.markdown("### Download Data Package")
                st.download_button(
                    label=f"Download Archive ({st.session_state.zip_filename})",
                    data=st.session_state.zip_buffer.getvalue(),
                    file_name=st.session_state.zip_filename,
                    mime="application/zip",
                    type="primary",
                    use_container_width=True,
                )

            # Progression Priorities Tab
            tab_priorities, tab_endpoints, tab_files = st.tabs([
                "Progression Priorities", "Endpoint Status", "File Previews"
            ])

            with tab_priorities:
                st.markdown("**Rule-Based Next Steps:**")
                priorities = summary.get("progression_priorities", [])
                for item in priorities:
                    st.info(item)

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
    st.subheader("Public Game Resources (Keyless)")
    st.markdown(
        "Extract official Hypixel SkyBlock item schemas, skill definitions, and collection unlock milestones. "
        "These public endpoints require **no API key**, **no Minecraft username**, and **no player authentication**."
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

    if st.button("Extract Public Resources", type="primary", use_container_width=True):
        if not selected_pub_categories:
            st.warning("Please select at least one public resource to extract.")
        else:
            pub_client = HypixelAPIClient(api_key=None)
            pub_progress = st.progress(0, text="Fetching public resources...")

            def update_pub_progress(step: int, total: int, category: str, status: str):
                pct = int((step / total) * 100)
                pub_progress.progress(pct, text=f"Fetching {category} ({step}/{total})")

            pub_extractor = ProfileExtractor(client=pub_client, progress_callback=update_pub_progress)
            with st.spinner("Querying Hypixel public resource endpoints..."):
                pub_results = pub_extractor.extract_public_resources(selected_pub_categories)
                pub_exporter = PublicResourceExporter(results=pub_results)
                pub_zip_buffer = pub_exporter.build_zip_in_memory()
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                pub_zip_name = f"SkyBlock_Public_Resources_{ts}.zip"

                st.session_state.public_results = pub_results
                st.session_state.public_zip_buffer = pub_zip_buffer
                st.session_state.public_zip_filename = pub_zip_name
                pub_progress.progress(100, text="Public resources extracted successfully.")

    if st.session_state.public_results:
        st.divider()
        st.subheader("Extracted Public Resources")

        pub_res = st.session_state.public_results
        successful_pub = sum(1 for r in pub_res.values() if r.status == "success")

        st.download_button(
            label=f"Download Public Resources Archive ({st.session_state.public_zip_filename})",
            data=st.session_state.public_zip_buffer.getvalue(),
            file_name=st.session_state.public_zip_filename,
            mime="application/zip",
            type="primary",
            use_container_width=True,
        )

        tab_pub_status, tab_pub_preview = st.tabs(["Extraction Status", "Schema Inspector"])
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

