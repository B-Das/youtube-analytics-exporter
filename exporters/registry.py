from typing import List, Dict
from exporters.base import BaseExporter
from exporters.overview import OverviewExporter
from exporters.content import ContentExporter
from exporters.reach import ReachExporter
from exporters.audience import AudienceExporter
from exporters.engagement import EngagementExporter
from exporters.geography import GeographyExporter
from exporters.traffic import TrafficExporter
from exporters.devices import DevicesExporter
from exporters.playlists import PlaylistsExporter
from exporters.daily_metrics import DailyMetricsExporter

ALL_EXPORTERS: List[BaseExporter] = [
    OverviewExporter(),
    ContentExporter(),
    ReachExporter(),
    AudienceExporter(),
    EngagementExporter(),
    GeographyExporter(),
    TrafficExporter(),
    DevicesExporter(),
    PlaylistsExporter(),
    DailyMetricsExporter(),
]

EXPORTER_MAP: Dict[str, BaseExporter] = {e.id: e for e in ALL_EXPORTERS}

def get_all_exporters() -> List[BaseExporter]:
    return ALL_EXPORTERS

def get_exporter_by_id(exp_id: str) -> BaseExporter:
    return EXPORTER_MAP.get(exp_id)
