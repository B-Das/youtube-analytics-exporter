import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from exporters.registry import get_all_exporters
from zip_archiver import build_analytics_zip
from youtube_auth import YouTubeAuthHandler

# Streamlit Page Configuration
st.set_page_config(
    page_title="YouTube Studio Analytics Exporter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .brand-title {
        color: #38bdf8;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .brand-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-top: 6px;
    }
    
    .stat-box {
        background: #1e293b;
        border: 1px solid #475569;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #38bdf8;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        font-weight: 600;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%);
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Check for OAuth callback code in URL query parameters
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    try:
        redirect_uri = YouTubeAuthHandler.get_redirect_uri()
        flow = YouTubeAuthHandler.create_oauth_flow(redirect_uri=redirect_uri)
        flow.fetch_token(code=auth_code)
        YouTubeAuthHandler.save_credentials(flow.credentials)
        st.query_params.clear()
        st.success("🎉 Authentication successful!")
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.query_params.clear()

# Check auth status
analytics_service, data_service, is_authenticated = YouTubeAuthHandler.get_services()
channel_info = None

if is_authenticated:
    channel_info = YouTubeAuthHandler.get_channel_info(data_service)

# Initialize Session States
if "date_start" not in st.session_state:
    st.session_state.date_start = (datetime.now() - timedelta(days=28)).date()
if "date_end" not in st.session_state:
    st.session_state.date_end = datetime.now().date()

# Sidebar Configuration
with st.sidebar:
    st.header("🔑 Authentication")
    
    if is_authenticated:
        if channel_info:
            st.markdown(f"""
            <div style="background-color: #1e293b; border: 1px solid #0284c7; border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
                <img src="{channel_info['thumbnail']}" style="border-radius: 50%; width: 44px; height: 44px; border: 2px solid #38bdf8;" />
                <div>
                    <div style="font-weight: bold; color: #f8fafc; font-size: 0.9rem; line-height: 1.2;">{channel_info['title']}</div>
                    <div style="color: #38bdf8; font-size: 0.8rem; font-weight: 500; margin-top: 2px;">🟢 Connected</div>
                    <div style="color: #94a3b8; font-size: 0.75rem;">{int(channel_info['subscribers']):,} subscribers</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            channel_name = channel_info['title'].replace(" ", "")
        else:
            st.success("🟢 Authenticated Successfully!")
            channel_name = "YouTubeChannel"
        
        if st.button("🚪 Log Out", use_container_width=True):
            import os
            if "creds" in st.session_state:
                del st.session_state["creds"]
            if os.path.exists(YouTubeAuthHandler.TOKEN_FILE):
                os.remove(YouTubeAuthHandler.TOKEN_FILE)
            st.rerun()
    else:
        st.warning("🔴 Not Connected to YouTube")
        channel_name = "YouTubeChannel"
        
        if YouTubeAuthHandler.is_client_secrets_present():
            redirect_uri = YouTubeAuthHandler.get_redirect_uri()
            try:
                flow = YouTubeAuthHandler.create_oauth_flow(redirect_uri=redirect_uri)
                auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
                
                st.link_button("🔑 Log in with Google", auth_url, use_container_width=True)
                st.caption("Opens Google login in your browser tab.")
                
                with st.expander("📌 Manual Auth Code Entry", expanded=False):
                    manual_code = st.text_input("Paste Authorization Code or Redirect URL:")
                    if st.button("Submit Auth Code", use_container_width=True):
                        if manual_code:
                            code_to_use = manual_code.strip()
                            if "code=" in code_to_use:
                                import urllib.parse
                                parsed = urllib.parse.urlparse(code_to_use)
                                query_dict = urllib.parse.parse_qs(parsed.query)
                                code_to_use = query_dict.get("code", [code_to_use])[0]
                            try:
                                flow.fetch_token(code=code_to_use)
                                YouTubeAuthHandler.save_credentials(flow.credentials)
                                st.success("🎉 Authentication successful!")
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Error exchanging code: {ex}")
            except Exception as e:
                st.error(f"Error setting up login link: {e}")
        else:
            st.error("Missing Google Client Secrets. Add `client_secrets` to Streamlit Secrets or upload `client_secrets.json`.")

    st.divider()
    st.markdown("### 📜 Rules Applied")
    st.info("✓ Exact YouTube Studio headers\n\n✓ YouTube Studio column ordering\n\n✓ Zero custom calculated metrics")

# Header Rendering
channel_title_header = channel_info['title'] if (is_authenticated and channel_info) else "YouTube Analytics"
st.markdown(f"""
<div class="main-header">
    <div class="brand-title">⚡ {channel_title_header} — One-Click Exporter (V1)</div>
    <div class="brand-subtitle">Download clean raw report packages matching YouTube Studio exactly. No renaming, no calculated columns.</div>
</div>
""", unsafe_allow_html=True)

# Authentication Guard
if not is_authenticated:
    st.info("👋 Welcome! Please log in with your Google account in the sidebar to access your channel's export dashboard.")
    st.stop()

# ----------------- Main Dashboard -----------------

st.subheader("📅 1. Select Date Range")
col_p1, col_p2, col_p3, col_p4, col_p5, col_p6, col_p7, col_p8 = st.columns(8)
today = datetime.now().date()

with col_p1:
    if st.button("Today", use_container_width=True):
        st.session_state.date_start = today
        st.session_state.date_end = today
with col_p2:
    if st.button("Yesterday", use_container_width=True):
        st.session_state.date_start = today - timedelta(days=1)
        st.session_state.date_end = today - timedelta(days=1)
with col_p3:
    if st.button("Last 7 Days", use_container_width=True):
        st.session_state.date_start = today - timedelta(days=7)
        st.session_state.date_end = today
with col_p4:
    if st.button("Last 28 Days", use_container_width=True):
        st.session_state.date_start = today - timedelta(days=28)
        st.session_state.date_end = today
with col_p5:
    if st.button("Last 90 Days", use_container_width=True):
        st.session_state.date_start = today - timedelta(days=90)
        st.session_state.date_end = today
with col_p6:
    if st.button("Last 365 Days", use_container_width=True):
        st.session_state.date_start = today - timedelta(days=365)
        st.session_state.date_end = today
with col_p7:
    if st.button("Lifetime", use_container_width=True):
        st.session_state.date_start = datetime(2024, 1, 1).date()
        st.session_state.date_end = today
with col_p8:
    st.markdown("**Custom**")

col_d1, col_d2 = st.columns(2)
with col_d1:
    st.session_state.date_start = st.date_input("Start Date", value=st.session_state.date_start)
with col_d2:
    st.session_state.date_end = st.date_input("End Date", value=st.session_state.date_end)

str_start = st.session_state.date_start.strftime("%Y-%m-%d")
str_end = st.session_state.date_end.strftime("%Y-%m-%d")

st.divider()

# Exporters Checklist
st.subheader("📋 2. Select Reports to Include")
all_exporters = get_all_exporters()

col_sel1, _ = st.columns([1, 4])
with col_sel1:
    select_all = st.checkbox("Check All", value=True)

selected_exporters = []
exp_cols = st.columns(3)
for idx, exp in enumerate(all_exporters):
    col = exp_cols[idx % 3]
    with col:
        is_checked = col.checkbox(f"**{exp.name}** (`{exp.filename}`)", value=select_all)
        if is_checked:
            selected_exporters.append(exp)

st.divider()

# Preview Summary
st.subheader("📊 3. Export Preview & Summary")
est_days = max(1, (st.session_state.date_end - st.session_state.date_start).days + 1)
est_files = len(selected_exporters) + 1
est_rows = sum([e.estimate_rows(str_start, str_end) for e in selected_exporters])
est_size_kb = max(2.5, est_rows * 0.11)

c_m1, c_m2, c_m3, c_m4 = st.columns(4)
with c_m1:
    st.markdown(f'<div class="stat-box"><div class="stat-label">Requested Time Range</div><div class="stat-value">{est_days} Days</div><div style="font-size:0.8rem; color:#94a3b8;">{str_start} → {str_end}</div></div>', unsafe_allow_html=True)
with c_m2:
    st.markdown(f'<div class="stat-box"><div class="stat-label">Estimated Files</div><div class="stat-value">{est_files} Files</div><div style="font-size:0.8rem; color:#94a3b8;">CSVs + metadata.json</div></div>', unsafe_allow_html=True)
with c_m3:
    st.markdown(f'<div class="stat-box"><div class="stat-label">Estimated Total Rows</div><div class="stat-value">~{est_rows:,}</div><div style="font-size:0.8rem; color:#94a3b8;">Raw CSV data rows</div></div>', unsafe_allow_html=True)
with c_m4:
    st.markdown(f'<div class="stat-box"><div class="stat-label">Estimated ZIP Size</div><div class="stat-value">~{est_size_kb:.1f} KB</div><div style="font-size:0.8rem; color:#94a3b8;">Compressed archive</div></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Progress checklist container
progress_placeholder = st.empty()

# Downloader Actions
col_act1, col_act2 = st.columns(2)

def progress_update_callback(name, current, total):
    with progress_placeholder.container():
        percent = int((current / total) * 100)
        st.markdown(f"**Exporting:** {name} ({current}/{total})")
        st.progress(percent)

with col_act1:
    if st.button("🚀 Download Everything (All Reports)", use_container_width=True):
        zip_bytes, stats = build_analytics_zip(
            selected_exporters=all_exporters,
            start_date=str_start,
            end_date=str_end,
            channel_name=channel_name,
            analytics_service=analytics_service,
            data_service=data_service,
            progress_callback=progress_update_callback
        )
        progress_placeholder.success("✔ Overview ✔ Content ✔ Reach ✔ Audience ✔ Daily Metrics ✔ ZIP Packaged!")
        st.download_button(
            label=f"💾 Save {stats['filename']} ({stats['size_kb']} KB)",
            data=zip_bytes,
            file_name=stats['filename'],
            mime="application/zip",
            use_container_width=True
        )

with col_act2:
    if st.button("📦 Download Selected Reports", use_container_width=True):
        if not selected_exporters:
            st.error("Please check at least one report exporter checkbox above!")
        else:
            zip_bytes, stats = build_analytics_zip(
                selected_exporters=selected_exporters,
                start_date=str_start,
                end_date=str_end,
                channel_name=channel_name,
                analytics_service=analytics_service,
                data_service=data_service,
                progress_callback=progress_update_callback
            )
            progress_placeholder.success(f"✔ Selected {len(selected_exporters)} reports packaged successfully!")
            st.download_button(
                label=f"💾 Save {stats['filename']} ({stats['size_kb']} KB)",
                data=zip_bytes,
                file_name=stats['filename'],
                mime="application/zip",
                use_container_width=True
            )

# Table preview
st.divider()
st.subheader("🔍 Selected Report Preview")

if selected_exporters:
    tabs = st.tabs([e.name for e in selected_exporters])
    for idx, exp in enumerate(selected_exporters):
        with tabs[idx]:
            try:
                df_preview = exp.export(
                    start_date=str_start,
                    end_date=str_end,
                    analytics_service=analytics_service,
                    data_service=data_service
                )
                st.dataframe(df_preview, use_container_width=True)
            except Exception as e:
                st.error(f"Failed to query {exp.name}: {e}")
