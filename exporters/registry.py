import os
from typing import List, Dict
from exporters.base import BaseExporter, SchemaExporter

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")

REPORT_FILES = [
    "overview.json",
    "content.json",
    "daily_metrics.json",
    "age.json",
    "gender.json",
    "geography.json",
    "traffic.json",
    "devices.json",
    "playlists.json"
]

ALL_EXPORTERS: List[BaseExporter] = []
EXPORTER_MAP: Dict[str, BaseExporter] = {}

for filename in REPORT_FILES:
    schema_path = os.path.join(SCHEMA_DIR, filename)
    if os.path.exists(schema_path):
        exporter = SchemaExporter(schema_path)
        ALL_EXPORTERS.append(exporter)
        EXPORTER_MAP[exporter.id] = exporter

def get_all_exporters() -> List[BaseExporter]:
    return ALL_EXPORTERS

def get_exporter_by_id(exp_id: str) -> BaseExporter:
    return EXPORTER_MAP.get(exp_id)
