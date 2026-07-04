import os
import sys
from datetime import datetime, timedelta
from exporters.registry import get_all_exporters
from zip_archiver import build_analytics_zip, sanitize_filename_component

def run_daily_export():
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dash_str = datetime.now().strftime("%Y-%m-%d")

    export_dir = os.path.join(os.getcwd(), "daily_exports")

    print(f"[{datetime.now().isoformat()}] Starting automated 9 PM YouTube Analytics Export...")

    from youtube_auth import YouTubeAuthHandler
    analytics_service, data_service, is_authenticated = YouTubeAuthHandler.get_services()
    
    if not is_authenticated:
        print(f"[{datetime.now().isoformat()}] [ERROR] YouTube API credentials not found. Please log in first via app.py.")
        sys.exit(1)

    channels = YouTubeAuthHandler.get_channels(data_service)
    if not channels:
        print(f"[{datetime.now().isoformat()}] [ERROR] No owned YouTube channels were returned by Data API v3.")
        sys.exit(1)

    all_exporters = get_all_exporters()
    for channel_info in channels:
        zip_bytes, stats = build_analytics_zip(
            selected_exporters=all_exporters,
            start_date=yesterday_str,
            end_date=today_dash_str,
            channel_info=channel_info,
            analytics_service=analytics_service,
            data_service=data_service
        )

        channel_folder = sanitize_filename_component(
            channel_info["title"],
            fallback=channel_info["id"]
        )
        channel_export_dir = os.path.join(export_dir, channel_folder)
        os.makedirs(channel_export_dir, exist_ok=True)
        out_zip_path = os.path.join(channel_export_dir, stats["filename"])
        with open(out_zip_path, "wb") as f:
            f.write(zip_bytes)

        print(f"[{datetime.now().isoformat()}] Success! Saved daily package to: {out_zip_path}")
        print(f"Reports: {stats['success_count']} succeeded | Total rows: {stats['total_rows']:,} | Size: {stats['size_mb']} MB")

if __name__ == "__main__":
    run_daily_export()
