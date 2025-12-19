import streamlit as st
import extract_profile
import time
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SkyBlock Profile Extractor",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    /* Global Styles */
    .stApp {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #e0e0e0;
    }

    /* Titles and Headings */
    h1, h2, h3 {
        color: #ffffff;
        text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
    }
    
    h1 {
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: glow 2s ease-in-out infinite alternate;
    }


    /* Input Fields */
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #ffffff;
        transition: all 0.3s ease;
    }

    .stTextInput > div > div > input:focus {
        border-color: #00d2ff;
        box-shadow: 0 0 10px rgba(0, 210, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.1);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #FF512F 0%, #DD2476 100%);
        color: white;
        border: none;
        padding: 0.6rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        transition: transform 0.2s, box-shadow 0.2s;
        box-shadow: 0 5px 15px rgba(221, 36, 118, 0.4);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(221, 36, 118, 0.6);
        background: linear-gradient(45deg, #FF512F 0%, #DD2476 100%); /* Maintain gradient */
        color: white;
    }

    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Secondary Button (if needed) */
    div[data-testid="stForm"] .stButton > button {
         background: linear-gradient(45deg, #00d2ff 0%, #3a7bd5 100%);
         box-shadow: 0 5px 15px rgba(58, 123, 213, 0.4);
    }

    /* Expander/Cards */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        color: #fff;
    }
    
    div[data-testid="stExpander"] {
        background-color: rgba(0, 0, 0, 0.2);
        border-radius: 10px;
        padding: 10px;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(22, 33, 62, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Success/Info Messages */
    .stSuccess {
        background-color: rgba(0, 200, 83, 0.1);
        border: 1px solid rgba(0, 200, 83, 0.3);
        color: #00e676;
    }
    
    .stInfo {
        background-color: rgba(41, 121, 255, 0.1);
        border: 1px solid rgba(41, 121, 255, 0.3);
        color: #448aff;
    }

    /* Radios */
    .stRadio > div {
        background-color: rgba(0,0,0,0.2);
        padding: 20px;
        border-radius: 10px;
    }

</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURATION ---
with st.sidebar:
    st.image("https://media.tenor.com/V7X8g2y0u90AAAAi/minecraft-sword.gif", width=50) # Just a fun placeholder or use an icon
    st.title("Settings")
    
    # Try to load API key
    default_key = ""
    try:
        if Path("api_key.txt").exists():
            default_key = Path("api_key.txt").read_text().strip()
    except:
        pass

    api_key_input = st.text_input("Hypixel API Key", value=default_key, type="password", help="Get this from developer.hypixel.net")
    
    if api_key_input and api_key_input != default_key:
        # Save new key
        try:
            with open("api_key.txt", "w") as f:
                f.write(api_key_input)
            st.toast("API Key saved!", icon="💾")
        except Exception as e:
            st.error(f"Could not save API key: {e}")

    st.markdown("---")
    st.markdown("### About")
    st.info("This tool extracts comprehensive SkyBlock profile data for analysis.")

# --- MAIN CONTENT ---
col1, col2 = st.columns([3, 1])

with col1:
    st.title("SkyBlock Profile Extractor")
    st.markdown("*Export your Hypixel SkyBlock data in seconds.*")

with col2:
    # Just a visual element
    pass

st.markdown("<br>", unsafe_allow_html=True)

# --- USER INPUT SECTION ---
with st.container():    
    c1, c2 = st.columns([3, 1])
    with c1:
        username = st.text_input("Minecraft Username", placeholder="e.g. Technoblade")
    with c2:
        st.write("") # Spacer
        st.write("") # Spacer
        fetch_btn = st.button("🔍 Find Profiles", use_container_width=True)

# --- SESSION STATE MANAGEMENT ---
if "profiles" not in st.session_state:
    st.session_state.profiles = None
if "uuid" not in st.session_state:
    st.session_state.uuid = None
if "real_username" not in st.session_state:
    st.session_state.real_username = None

# --- LOGIC: FETCH PROFILES ---
if fetch_btn and username and api_key_input:
    with st.spinner("Talking to Mojang & Hypixel..."):
        try:
            # Get UUID
            uuid_fmt, uuid_raw = extract_profile.get_player_uuid(username)
            st.session_state.uuid = uuid_fmt
            
            # Get Profiles
            profiles = extract_profile.get_profiles(uuid_fmt, api_key_input)
            st.session_state.profiles = profiles
            st.session_state.real_username = username # Could extract real name from API if function returned it
            
            st.success(f"Found {len(profiles)} profiles for {username}!")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.session_state.profiles = None

elif fetch_btn and not api_key_input:
    st.warning("Please enter your Hypixel API Key in the sidebar.")

# --- LOGIC: SELECT AND EXTRACT ---
if st.session_state.profiles:
    st.divider()
    st.subheader("Select Profile")
    
    # Create friendly labels for the radio button
    profile_options = {
        f"{p['name']} ({p['game_mode']}) - Last Save: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p['last_save']/1000))}": p 
        for p in st.session_state.profiles
    }
    
    selected_label = st.radio(
        "Choose a profile to download:", 
        options=list(profile_options.keys()),
        index=0
    )
    
    if selected_label:
        selected_profile = profile_options[selected_label]
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚀 Extract Data", type="primary", use_container_width=True):
            output_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            try:
                # We can't easily get real-time progress from the function without modifying it,
                # so we'll simulate a bit or just run it.
                # For a better UX, let's wrap the extraction logic here or trust the function is fast.
                
                with st.spinner("Extracting data... (This might take a moment)"):
                    # Call the extraction function
                    # Note: We need to handle the prints inside extract_main or just let it run.
                    # Since we imported extract_profile, we can call extract_data directly.
                    
                    out_dir, count = extract_profile.extract_data(
                        st.session_state.uuid, 
                        selected_profile, 
                        api_key_input, 
                        st.session_state.real_username or username
                    )
                    
                    progress_bar.progress(100)
                    
                    st.balloons()
                    
                    st.markdown(f"""
                    <div style="background-color: rgba(0, 255, 127, 0.2); padding: 20px; border-radius: 10px; border: 1px solid #00ff7f; text-align: center;">
                        <h2 style="margin:0; color: #00ff7f;">Success!</h2>
                        <p style="font-size: 1.2em;">Extracted <b>{count}</b> files.</p>
                        <p style="font-family: monospace; background: rgba(0,0,0,0.5); padding: 5px; border-radius: 5px;">{out_dir}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("📂 View Extracted Files"):
                        # List files in the output directory
                        files = sorted([f.name for f in out_dir.iterdir() if f.is_file()])
                        for f in files:
                            st.code(f, language="text")

            except Exception as e:
                st.error(f"Extraction failed: {str(e)}")

# --- FOOTER ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 0.8em;">
    SkyBlock Profile Extractor • Built with Streamlit • Designed for Sahaj33
</div>
""", unsafe_allow_html=True)
