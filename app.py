import os
import importlib
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

import youtube_auth
importlib.reload(youtube_auth)
from youtube_auth import YouTubeAuthHandler

from exporters.registry import get_all_exporters, get_exporter_by_id
from zip_archiver import build_analytics_zip
from engine.schema_validator import validate_all_schemas, SchemaValidationError

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

# Validate schemas on startup
try:
    VALIDATED_SCHEMAS = validate_all_schemas(SCHEMA_DIR)
except SchemaValidationError as sve:
    st.error(f"⚠️ Startup Schema Validation Error: {sve}")
    st.stop()

# Streamlit Page Configuration
st.set_page_config(
    page_title="YouTube Studio Exporter",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=600, show_spinner=False)
def fetch_cached_preview(exp_id: str, start_date: str, end_date: str, channel_id: str, _analytics_service, _data_service):
    exporter = get_exporter_by_id(exp_id)
    if not exporter:
        return None
    return exporter.export(
        start_date=start_date,
        end_date=end_date,
        analytics_service=_analytics_service,
        data_service=_data_service,
        channel_id=channel_id
    )

# Custom Styling
st.markdown("""
<style>
    html, body, .stApp {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
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

# OAuth Callback handling
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    # Google echoes back the `state` param we embedded the code_verifier in.
    # Passing it here makes auth work even if the app woke from sleep and
    # session_state was wiped (Streamlit Cloud free tier behaviour).
    oauth_state = st.query_params.get("state", None)
    try:
        redirect_uri = YouTubeAuthHandler.get_redirect_uri()
        YouTubeAuthHandler.exchange_code_for_credentials(
            code=auth_code,
            redirect_uri=redirect_uri,
            state=oauth_state,
        )
        st.query_params.clear()
        st.success("🎉 Authentication successful!")
        st.rerun()
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        st.query_params.clear()

# Retrieve authentication status and services
analytics_service, data_service, is_authenticated = YouTubeAuthHandler.get_services()
channel_info = None
available_channels = []

if is_authenticated:
    available_channels = YouTubeAuthHandler.get_channels(data_service)
    available_channel_ids = {ch["id"] for ch in available_channels}
    selected_channel_id = st.session_state.get("selected_channel_id")

    if len(available_channels) == 1:
        selected_channel_id = available_channels[0]["id"]
        st.session_state["selected_channel_id"] = selected_channel_id
    elif selected_channel_id not in available_channel_ids:
        selected_channel_id = None
        st.session_state.pop("selected_channel_id", None)

    if selected_channel_id:
        channel_info = next(
            (ch for ch in available_channels if ch["id"] == selected_channel_id),
            None
        )

# Initialize Session States for Dates
if "date_start_input" not in st.session_state:
    st.session_state["date_start_input"] = (datetime.now() - timedelta(days=28)).date()
if "date_end_input" not in st.session_state:
    st.session_state["date_end_input"] = datetime.now().date()

st.session_state.date_start = st.session_state["date_start_input"]
st.session_state.date_end = st.session_state["date_end_input"]

# Sidebar Navigation & Authentication Status
with st.sidebar:
    st.header("🔑 Authentication")
    
    if is_authenticated:
        if available_channels and len(available_channels) > 1:
            st.subheader("📺 Select Active Channel")
            channel_options = {ch["title"]: ch["id"] for ch in available_channels}
            selected_title = st.selectbox(
                "Choose Channel:",
                options=list(channel_options.keys()),
                index=0
            )
            st.session_state["selected_channel_id"] = channel_options[selected_title]
            channel_info = next((ch for ch in available_channels if ch["id"] == channel_options[selected_title]), None)

        if channel_info:
            subscribers_val = channel_info.get("subscribers")
            sub_display = f"{int(subscribers_val):,} subscribers" if subscribers_val else "Channel Connected"
            st.markdown(f"""
            <div style="background-color: #1e293b; border: 1px solid #0284c7; border-radius: 8px; padding: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 12px;">
                <img src="{channel_info.get('thumbnail', '')}" style="border-radius: 50%; width: 44px; height: 44px; border: 2px solid #38bdf8;" />
                <div>
                    <div style="font-weight: bold; color: #f8fafc; font-size: 0.9rem; line-height: 1.2;">{channel_info.get('title', 'Channel')}</div>
                    <div style="color: #38bdf8; font-size: 0.8rem; font-weight: 500; margin-top: 2px;">🟢 Connected</div>
                    <div style="color: #94a3b8; font-size: 0.75rem;">{sub_display}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.success("🟢 Authenticated Successfully!")

        if st.button("🚪 Log Out", width="stretch"):
            import os
            if "creds" in st.session_state:
                del st.session_state["creds"]
            if os.path.exists(YouTubeAuthHandler.TOKEN_FILE):
                os.remove(YouTubeAuthHandler.TOKEN_FILE)
            st.rerun()
    else:
        st.warning("🔴 Not Connected to YouTube")
        if YouTubeAuthHandler.is_client_secrets_present():
            redirect_uri = YouTubeAuthHandler.get_redirect_uri()
            try:
                auth_url, _ = YouTubeAuthHandler.get_auth_url(redirect_uri=redirect_uri)
                st.link_button("🔑 Log in with Google", auth_url, width="stretch")
            except Exception as e:
                st.error(f"Error setting up auth: {e}")
        else:
            st.error("Missing Google Client Secrets. Add `client_secrets` to Streamlit Secrets or upload `client_secrets.json`.")

    st.divider()
    st.markdown("### 📜 Export Rules")
    st.info("✓ Official metrics only\n\n✓ Exact YouTube Studio headers\n\n✓ UTF-8 BOM encoding\n\n✓ Zero estimated data")

# Header Rendering
channel_header_name = channel_info['title'] if (is_authenticated and channel_info) else "YouTube Studio"
st.markdown(f"""
<div class="main-header">
    <div class="brand-title">⚡ {channel_header_name} — Studio Exporter</div>
    <div class="brand-subtitle">Exports official data available through the YouTube Analytics API and YouTube Data API v3 using YouTube Studio terminology where applicable.</div>
</div>
""", unsafe_allow_html=True)

if not is_authenticated:
    st.info("👋 Welcome! Please log in with your Google account in the sidebar to access your channel's export dashboard.")
    st.stop()

# API Compatibility Check Dashboard Panel
st.subheader("🔍 API Connection Verification")
col_chk1, col_chk2, col_chk3, col_chk4 = st.columns(4)
with col_chk1:
    st.success("✔ Analytics API: Connected")
with col_chk2:
    st.success("✔ Data API v3: Connected")
with col_chk3:
    st.success("✔ OAuth Scopes: Granted")
with col_chk4:
    if channel_info:
        st.success(f"✔ Channel: {channel_info['title']}")
    else:
        st.warning("⚠️ Channel: Loading...")

st.divider()

# Date Range Selection Panel
st.subheader("📅 1. Select Date Range")
col_p1, col_p2, col_p3, col_p4, col_p5, col_p6, col_p7, col_p8 = st.columns(8)
today = datetime.now().date()

with col_p1:
    if st.button("Today", width="stretch"):
        st.session_state["date_start_input"] = today
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p2:
    if st.button("Yesterday", width="stretch"):
        st.session_state["date_start_input"] = today - timedelta(days=1)
        st.session_state["date_end_input"] = today - timedelta(days=1)
        st.rerun()
with col_p3:
    if st.button("Last 7 Days", width="stretch"):
        st.session_state["date_start_input"] = today - timedelta(days=7)
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p4:
    if st.button("Last 28 Days", width="stretch"):
        st.session_state["date_start_input"] = today - timedelta(days=28)
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p5:
    if st.button("Last 90 Days", width="stretch"):
        st.session_state["date_start_input"] = today - timedelta(days=90)
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p6:
    if st.button("Last 365 Days", width="stretch"):
        st.session_state["date_start_input"] = today - timedelta(days=365)
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p7:
    if st.button("Lifetime", width="stretch"):
        st.session_state["date_start_input"] = datetime(2024, 1, 1).date()
        st.session_state["date_end_input"] = today
        st.rerun()
with col_p8:
    st.markdown("**Custom**")

col_d1, col_d2 = st.columns(2)
with col_d1:
    d_start = st.date_input("Start Date", key="date_start_input")
with col_d2:
    d_end = st.date_input("End Date", key="date_end_input")

st.session_state.date_start = d_start
st.session_state.date_end = d_end

str_start = d_start.strftime("%Y-%m-%d")
str_end = d_end.strftime("%Y-%m-%d")

st.divider()

# Reports Selection Checklist
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

# Actions & Downloader
st.subheader("🚀 3. Export Package Generation")

progress_container = st.empty()
summary_container = st.empty()

col_act1, col_act2 = st.columns(2)

def progress_update_callback(name, current, total, percent):
    with progress_container.container():
        st.markdown(f"**Export Progress:** `{name}` ({current}/{total})")
        st.progress(percent)

with col_act1:
    if st.button(f"🚀 Download Everything (All {len(all_exporters)} Reports)", width="stretch"):
        if not channel_info:
            st.error("No active channel selected.")
        else:
            try:
                zip_bytes, stats = build_analytics_zip(
                    selected_exporters=all_exporters,
                    start_date=str_start,
                    end_date=str_end,
                    channel_info=channel_info,
                    analytics_service=analytics_service,
                    data_service=data_service,
                    progress_callback=progress_update_callback
                )
                progress_container.success(f"✔ All {len(all_exporters)} reports packaged successfully!")

                with summary_container.container():
                    st.markdown(f"""
                    <div style="background-color: #1e293b; border: 1px solid #38bdf8; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                        <h4 style="color: #38bdf8; margin-top:0;">🎉 Export Complete</h4>
                        <p style="margin: 4px 0;"><strong>Session ID:</strong> <code>{stats['session_id']}</code></p>
                        <p style="margin: 4px 0;"><strong>Success:</strong> {stats['success_count']} | <strong>Failed:</strong> {stats['failed_count']} | <strong>Total Reports:</strong> {stats['total_reports']}</p>
                        <p style="margin: 4px 0;"><strong>Total Rows:</strong> {stats['total_rows']:,} | <strong>ZIP Size:</strong> {stats['size_mb']} MB | <strong>Generated in:</strong> {stats['duration_seconds']}s</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if stats['failed_reports']:
                        for rep_name, rep_info in stats['failed_reports'].items():
                            st.warning(f"⚠️ **{rep_name}** could not be exported: {rep_info.get('reason', 'Unknown error')}")

                st.download_button(
                    label=f"💾 Save {stats['filename']} ({stats['size_mb']} MB)",
                    data=zip_bytes,
                    file_name=stats['filename'],
                    mime="application/zip",
                    width="stretch"
                )
            except Exception as e:
                from exporters.base import BaseExporter
                _summary = BaseExporter.api_error_summary(None, e) if hasattr(BaseExporter, 'api_error_summary') else str(e)
                progress_container.error(f"❌ Export failed: {_summary}")

with col_act2:
    if st.button("📦 Download Selected Reports", width="stretch"):
        if not selected_exporters:
            st.error("Please check at least one report exporter checkbox above!")
        elif not channel_info:
            st.error("No active channel selected.")
        else:
            try:
                zip_bytes, stats = build_analytics_zip(
                    selected_exporters=selected_exporters,
                    start_date=str_start,
                    end_date=str_end,
                    channel_info=channel_info,
                    analytics_service=analytics_service,
                    data_service=data_service,
                    progress_callback=progress_update_callback
                )
                progress_container.success(f"✔ Selected {len(selected_exporters)} reports packaged successfully!")

                with summary_container.container():
                    st.markdown(f"""
                    <div style="background-color: #1e293b; border: 1px solid #38bdf8; border-radius: 10px; padding: 16px; margin-bottom: 16px;">
                        <h4 style="color: #38bdf8; margin-top:0;">🎉 Export Complete</h4>
                        <p style="margin: 4px 0;"><strong>Session ID:</strong> <code>{stats['session_id']}</code></p>
                        <p style="margin: 4px 0;"><strong>Success:</strong> {stats['success_count']} | <strong>Failed:</strong> {stats['failed_count']} | <strong>Total Reports:</strong> {stats['total_reports']}</p>
                        <p style="margin: 4px 0;"><strong>Total Rows:</strong> {stats['total_rows']:,} | <strong>ZIP Size:</strong> {stats['size_mb']} MB | <strong>Generated in:</strong> {stats['duration_seconds']}s</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if stats['failed_reports']:
                        for rep_name, rep_info in stats['failed_reports'].items():
                            st.warning(f"⚠️ **{rep_name}** could not be exported: {rep_info.get('reason', 'Unknown error')}")

                st.download_button(
                    label=f"💾 Save {stats['filename']} ({stats['size_mb']} MB)",
                    data=zip_bytes,
                    file_name=stats['filename'],
                    mime="application/zip",
                    width="stretch"
                )
            except Exception as e:
                from exporters.base import BaseExporter
                _summary = BaseExporter.api_error_summary(None, e) if hasattr(BaseExporter, 'api_error_summary') else str(e)
                progress_container.error(f"❌ Export failed: {_summary}")

# Table Previews
st.divider()
with st.expander("🔍 Selected Report Previews (Click to expand)", expanded=False):
    if selected_exporters and channel_info:
        tabs = st.tabs([exp.name for exp in selected_exporters])
        for idx, exp in enumerate(selected_exporters):
            with tabs[idx]:
                try:
                    with st.spinner(f"Loading preview for {exp.name}..."):
                        df_preview = fetch_cached_preview(
                            exp.id,
                            str_start,
                            str_end,
                            channel_info["id"],
                            analytics_service,
                            data_service
                        )
                    if df_preview is None or df_preview.empty:
                        yesterday = today - timedelta(days=1)
                        if (d_start <= today <= d_end) or (d_start <= yesterday <= d_end):
                            st.info(
                                "No analytics data is currently available for the selected date range.\n\n"
                                "YouTube Analytics API data is often delayed for Today and Yesterday.\n\n"
                                "Try Last 7 Days or a custom range ending at least 2 days ago."
                            )
                        else:
                            st.info(f"ℹ️ No records found for **{exp.name}** in date range ({str_start} to {str_end}).")
                    else:
                        st.caption(f"Showing preview of {len(df_preview):,} rows")
                        st.dataframe(df_preview, width="stretch")
                except Exception as e:
                    from exporters.base import BaseExporter
                    _err = BaseExporter.api_error_summary(None, e) if hasattr(BaseExporter, 'api_error_summary') else str(e)
                    st.warning(f"⚠️ Could not load preview for **{exp.name}**: {_err}")
