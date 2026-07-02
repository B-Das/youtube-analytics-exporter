import os
import sys
from datetime import datetime, timedelta
from exporters.registry import get_all_exporters
from zip_archiver import build_analytics_zip

def run_daily_export():
    today_str = datetime.now().strftime("%Y_%m_%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_dash_str = datetime.now().strftime("%Y-%m-%d")

    export_dir = os.path.join(os.getcwd(), "daily_exports")
    os.makedirs(export_dir, exist_ok=True)

    print(f"[{datetime.now().isoformat()}] Starting automated 9 PM YouTube Analytics Export...")

    all_exporters = get_all_exporters()
    zip_bytes, stats = build_analytics_zip(
        selected_exporters=all_exporters,
        start_date=yesterday_str,
        end_date=today_dash_str,
        channel_name="HistoricHeights",
        use_mock=True  # Will use API if token.pickle exists
    )

    out_zip_path = os.path.join(export_dir, f"youtube_daily_{today_str}.zip")
    with open(out_zip_path, "wb") as f:
        f.write(zip_bytes)

    print(f"[{datetime.now().isoformat()}] Success! Saved daily package to: {out_zip_path}")
    print(f"Total files: {stats['file_count']} | Total rows: {stats['row_count']} | Size: {stats['size_kb']} KB")

if __name__ == "__main__":
    run_daily_export()
