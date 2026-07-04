import io
import json
import re
import time
import hashlib
import uuid
import zipfile
import datetime
from typing import List, Tuple
import pandas as pd
from exporters.base import BaseExporter

UNAVAILABLE_METRICS_LIST = [
    {
        "metric": "Impressions",
        "status": "Unavailable",
        "reason": "Not exposed by YouTube Analytics API."
    },
    {
        "metric": "Impressions click-through rate",
        "status": "Unavailable",
        "reason": "Not exposed by YouTube Analytics API."
    },
    {
        "metric": "Stayed to watch",
        "status": "Unavailable",
        "reason": "Not exposed by YouTube Analytics API."
    },
    {
        "metric": "Videos added",
        "status": "Unavailable",
        "reason": "Not exposed as a channel daily metric by YouTube Analytics API."
    },
    {
        "metric": "Videos published",
        "status": "Unavailable",
        "reason": "Not exposed as a channel daily metric by YouTube Analytics API."
    }
]

def sanitize_filename_component(value: str, fallback: str = "YouTubeChannel") -> str:
    """Sanitize channel name to be safe for OS filesystems."""
    if not value:
        return fallback
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or fallback

def generate_session_id() -> str:
    now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    random_hex = uuid.uuid4().hex[:4].upper()
    return f"EXP-{now_str}-{random_hex}"

def build_analytics_zip(
    selected_exporters: List[BaseExporter],
    start_date: str,
    end_date: str,
    channel_info: dict,
    analytics_service=None,
    data_service=None,
    progress_callback=None
) -> Tuple[bytes, dict]:
    """
    Executes all selected exporters, builds manifest.json and metadata.json,
    and packages everything into an in-memory ZIP file with UTF-8 BOM CSVs.
    """
    session_id = generate_session_id()
    started_at = time.perf_counter()
    zip_buffer = io.BytesIO()

    file_manifest = []
    failed_reports = {}
    warnings = []

    total_rows = 0
    total_bytes = 0
    success_count = 0
    failed_count = 0
    total_exporters = len(selected_exporters)

    now_dt = datetime.datetime.now().astimezone()
    iso_timestamp = now_dt.isoformat()
    tz_name = now_dt.tzname() or "UTC"

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, exporter in enumerate(selected_exporters):
            percent = int(((idx + 1) / total_exporters) * 100)
            if progress_callback:
                progress_callback(exporter.name, idx + 1, total_exporters, percent)

            try:
                df: pd.DataFrame = exporter.export(
                    start_date=start_date,
                    end_date=end_date,
                    analytics_service=analytics_service,
                    data_service=data_service,
                    channel_id=channel_info.get("id")
                )

                if df.empty:
                    warnings.append(f"{exporter.name} report returned no data for range ({start_date} to {end_date}).")

                # UTF-8 BOM encoding for Excel compatibility
                csv_str = df.to_csv(index=False)
                csv_bytes = csv_str.encode("utf-8-sig")

                zip_file.writestr(exporter.filename, csv_bytes)

                row_count = len(df)
                byte_count = len(csv_bytes)
                total_rows += row_count
                total_bytes += byte_count
                success_count += 1

                checksum = hashlib.sha256(csv_bytes).hexdigest()

                file_manifest.append({
                    "name": exporter.filename,
                    "report": exporter.name,
                    "rows": row_count,
                    "bytes": byte_count,
                    "checksum": checksum
                })
            except Exception as e:
                failed_count += 1
                err_text = str(e).splitlines()[0] if str(e) else "Unknown API Error"
                failed_reports[exporter.name] = {
                    "status": "Failed",
                    "reason": err_text
                }
                if progress_callback:
                    progress_callback(f"{exporter.name} (Failed)", idx + 1, total_exporters, percent)

        export_duration = round(time.perf_counter() - started_at, 2)

        # Generate manifest.json
        manifest_data = {
            "Export Session": session_id,
            "Generated At": iso_timestamp,
            "Encoding": "UTF-8 BOM",
            "Schema Version": "1.0",
            "Files": file_manifest,
            "Rows": total_rows,
            "Bytes": total_bytes
        }
        manifest_bytes = json.dumps(manifest_data, indent=2).encode("utf-8")
        zip_file.writestr("manifest.json", manifest_bytes)

        # Generate metadata.json
        metadata_data = {
            "Export Session": session_id,
            "Channel": channel_info.get("title", "YouTube Channel"),
            "Channel ID": channel_info.get("id", ""),
            "Channel Handle": channel_info.get("handle", ""),
            "Generated At": iso_timestamp,
            "Time Zone": tz_name,
            "Date Range": f"{start_date}_to_{end_date}",
            "Application Version": "1.0.0",
            "Export Schema Version": "1.0",
            "YouTube Analytics API": "Enabled",
            "YouTube Data API": "Enabled",
            "Unavailable Metrics": UNAVAILABLE_METRICS_LIST,
            "Failed Reports": failed_reports,
            "Warnings": warnings,
            "Export Duration Seconds": export_duration
        }
        metadata_bytes = json.dumps(metadata_data, indent=2).encode("utf-8")
        zip_file.writestr("metadata.json", metadata_bytes)

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()

    sanitized_channel = sanitize_filename_component(
        channel_info.get("title", "YouTubeChannel"),
        fallback=channel_info.get("id", "Channel")
    )
    zip_filename = f"{sanitized_channel}_{start_date}_to_{end_date}.zip"

    summary_stats = {
        "session_id": session_id,
        "filename": zip_filename,
        "success_count": success_count,
        "failed_count": failed_count,
        "total_reports": total_exporters,
        "total_rows": total_rows,
        "size_mb": round(len(zip_bytes) / (1024.0 * 1024.0), 2),
        "duration_seconds": export_duration,
        "failed_reports": failed_reports,
        "warnings": warnings
    }

    return zip_bytes, summary_stats
