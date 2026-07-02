import io
import json
import zipfile
from datetime import datetime, timezone
from typing import List, Tuple
import pandas as pd
from exporters.base import BaseExporter

def build_analytics_zip(
    selected_exporters: List[BaseExporter],
    start_date: str,
    end_date: str,
    channel_name: str = "HistoricHeights",
    analytics_service=None,
    data_service=None,
    use_mock: bool = True,
    progress_callback=None
) -> Tuple[bytes, dict]:
    """
    Executes all selected exporters, builds metadata.json, and packages everything
    into an in-memory ZIP file bytes.
    """
    zip_buffer = io.BytesIO()
    file_manifest = []
    total_rows = 0
    total_exporters = len(selected_exporters)

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for idx, exporter in enumerate(selected_exporters):
            if progress_callback:
                progress_callback(exporter.name, idx + 1, total_exporters)
            try:
                df: pd.DataFrame = exporter.export(
                    start_date=start_date,
                    end_date=end_date,
                    analytics_service=analytics_service,
                    data_service=data_service,
                    use_mock=use_mock
                )
                
                csv_bytes = df.to_csv(index=False).encode('utf-8')
                zip_file.writestr(exporter.filename, csv_bytes)

                row_count = len(df)
                total_rows += row_count
                file_manifest.append({
                    "Report Name": exporter.name,
                    "Filename": exporter.filename,
                    "Rows": row_count
                })
            except Exception as e:
                print(f"Error packaging {exporter.name}: {e}")

        # Construct exact Version 1 metadata.json
        metadata = {
            "Generated At": datetime.now(timezone.utc).isoformat(),
            "Channel": channel_name,
            "Date Range": {
                "start": start_date,
                "end": end_date
            },
            "API Version": "YouTube Analytics API v2 / Data v3",
            "Export Version": "1.0.0",
            "Total Files": len(file_manifest) + 1,
            "Total Rows": total_rows,
            "Manifest": file_manifest
        }

        metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
        zip_file.writestr("metadata.json", metadata_bytes)

    zip_buffer.seek(0)
    zip_bytes = zip_buffer.getvalue()
    
    summary_stats = {
        "file_count": len(file_manifest) + 1,
        "row_count": total_rows,
        "size_kb": round(len(zip_bytes) / 1024.0, 2),
        "filename": f"{channel_name}_{start_date}_to_{end_date}.zip"
    }
    
    return zip_bytes, summary_stats
